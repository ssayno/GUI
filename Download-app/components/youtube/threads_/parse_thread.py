from PyQt6.QtCore import pyqtSignal, QThread
import requests
import re
import json
from urllib.parse import unquote
import js2py
from unicodedata import normalize


class ThreadParseQuality(QThread):
    video_urls_signal = pyqtSignal(dict)
    audio_urls_signal = pyqtSignal(list)
    title_signal = pyqtSignal(str)

    def __init__(self, vu, parent=None):
        super().__init__(parent=parent)
        self.video_url = vu

    def run(self) -> None:
        resp = requests.get(self.video_url)
        html_text = resp.text
        csp_nonce = re.search('"cspNonce":"(.*?)","canaryState"', html_text).group(1)
        patten = re.compile(
            f'<script nonce="{csp_nonce}">var ytInitialPlayerResponse = (.*?);</script>'
        )
        base_js_script = 'https://youtube.com' + re.search(f'"jsUrl":"(.*?)"', html_text).group(1)
        js_executor = self.get_s_to_sig_js_code(base_js_script)
        # get self.js_executor
        json_data = json.loads(
            patten.search(html_text).group(1)
        )
        streaming_data = json_data['streamingData']
        adaptiveFormats = streaming_data['adaptiveFormats']
        title = normalize(
            'NFD', re.sub('[\【】/]（）', '', json_data['videoDetails']['title'])
        )
        self.title_signal.emit(title)
        video_urls = {}
        audio_urls = []
        qualities = []
        print(adaptiveFormats)
        for _format in adaptiveFormats:
            quote_url = _format.get('url', None)
            quality = _format['quality']
            qualities.append(quality)
            contentLength = _format.get('contentLength', None)
            if contentLength is None:
                continue
            if quote_url is None:
                s, _url = re.search('^s=(.*?)&sp=sig&?url=(.*?)$', _format['signatureCipher']).groups()
                sig_ = js_executor(unquote(s))
                url__ = unquote(
                    f'{_url}&sig={sig_}'
                )
            else:
                url__ = unquote(quote_url)
            mimeType = _format['mimeType']
            if 'video' in mimeType:
                quality_list = video_urls.get(quality, None)
                if quality_list is None:
                    video_urls[quality] = []
                video_urls[quality].append({
                    'url': url__,
                    'length': contentLength
                })
            elif 'audio' in mimeType:
                audio_urls.append({
                    'url': url__,
                    'length': contentLength
                })
        self.video_urls_signal.emit(video_urls)
        self.audio_urls_signal.emit(audio_urls)

    def get_s_to_sig_js_code(self, js_url):
        resp = requests.get(js_url)
        js_code = resp.text
        main_code_group = re.search(
            '(?P<maincode>(?P<functionName>\w+?)=function\(a\){a=a\.split\(""\);(?P<objName>\w+?)\..*?return a\.join\(""\)};)',
            js_code)
        # get main code
        main_code = main_code_group.group('maincode')
        function_name = main_code_group.group('functionName')
        obj_name = main_code_group.group('objName')
        # get obj code
        obj_patten = re.compile(fr'(var {obj_name}={{.*?}};)', flags=re.DOTALL)
        obj_code_group = obj_patten.search(js_code)
        obj_code = obj_code_group.group(1).replace('\n', ' ')

        def convert_s_to_sig(argument):
            complete_js_code = f'''\
    {obj_code}
    {main_code}
    (function(){{ return {function_name}('{argument}') }})();
            '''
            sig_ = js2py.eval_js(complete_js_code)
            return sig_

        return convert_s_to_sig