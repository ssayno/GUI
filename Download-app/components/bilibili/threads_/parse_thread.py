from PyQt6.QtCore import QThread, pyqtSignal
import requests
import re
import json
from urllib.parse import unquote


class BilibiliParseThread(QThread):
    bilibili_video_urls_signal = pyqtSignal(dict)
    bilibili_audio_urls_signal = pyqtSignal(list)

    def __init__(self, vu, parent=None):
        super().__init__(parent=parent)
        self.video_url = vu

    def run(self) -> None:
        cookies = {
            'SESSDATA': '8a984b63%2C1695826787%2C899f0%2A31'
        }
        resp = requests.get(self.video_url, cookies=cookies)
        html_text = resp.text
        we_need_json = json.loads(
            re.search('<script>window.__playinfo__=(.*?)</script>', html_text).group(1)
        )
        video_urls = {}
        audio_urls = []
        dash = we_need_json['data']['dash']
        video_json = dash['video']
        audio_json = dash['audio']
        for video_format in video_json:
            quality_id = video_format.get('id', None)
            real_video_url = unquote(
                video_format.get('baseUrl', video_format.get('base_url'))
            )
            bandWidth = video_format.get('bandwidth', None)
            if video_urls.get(quality_id, None) is None:
                video_urls[quality_id] = []
            video_urls[quality_id].append({
                "url": real_video_url,
                'bandwidth': bandWidth
            })
            pass
        for audio_format in audio_json:
            bandWidth = audio_format.get('bandwidth', None)
            real_audio_url = unquote(
                audio_format.get('baseUrl',
                                 audio_format.get('base_url'))
            )
            audio_urls.append({
                "url": real_audio_url,
                "bandwidth": bandWidth
            })
        self.bilibili_video_urls_signal.emit(video_urls)
        self.bilibili_audio_urls_signal.emit(audio_urls)
