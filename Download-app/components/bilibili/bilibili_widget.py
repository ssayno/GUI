import os
from PyQt6.QtWidgets import (
    QWidget, QLineEdit, QVBoxLayout, QComboBox, QPushButton, QHBoxLayout, QPlainTextEdit
)
from PyQt6.QtGui import (
    QRegularExpressionValidator
)
from PyQt6.QtCore import Qt, QThreadPool
from PyQt6.QtCore import QRegularExpression, QProcess
from .threads_.parse_thread import BilibiliParseThread
from .threads_.download_video_and_audio import DownloadBiliBiliVideoRunnable, DownloadBiliBiliAudioRunnable
from .subwidgets.progressBar import OwnProgressbar
from copy import deepcopy
import requests


class BilibiliWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        #
        self.p = None
        self.app_path = os.path.abspath('.')
        #
        self.origin_headers = {
            'Host': 'cn-lnsy-cm-01-03.bilivideo.com',
            'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
            'sec-ch-ua-platform': '"macOS"',
            'accept': '*/*',
            'origin': 'https://www.bilibili.com',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.bilibili.com/',
            'accept-language': 'zh-CN,zh;q=0.9',
            'if-range': 'Thu, 30 Mar 2023 20:40:59 GMT',
        }
        #
        self.title = 'UnKnow-bilibili'
        self.chunk_size = 100000
        self.video_contents = {}
        self.video_length = 0
        self.audio_length = 0
        self.audio_path = None
        self.video_path = None
        self.audio_contents = {}
        # threadpool
        self.video_threadpool = QThreadPool()
        self.video_threadpool.setMaxThreadCount(40)
        self.audio_threadpool = QThreadPool()
        self.audio_threadpool.setMaxThreadCount(40)
        #
        self.bilibili_video_urls = []
        self.bilibili_audio_urls = []
        current_path = os.path.dirname(__file__)
        with open(os.path.join(current_path, 'bilibili.css'), 'r') as f:
            self.setStyleSheet(f.read())
        self.regex_validator = QRegularExpressionValidator(
            QRegularExpression(
                '^https://www.bilibili.com/video/[a-zA-Z0-9-_]+'
            )
        )
        #
        self.__layout = QVBoxLayout()
        self.__layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        #
        self.bili_search_line = QLineEdit()
        self.bili_search_line.setObjectName('bilibili-searchLine')
        self.bili_search_button = QPushButton("开始解析")
        self.bili_search_button.setObjectName('bilibili-searchButton')
        self.bilibili_video_combobox = QComboBox()
        self.bilibili_progress_bar = OwnProgressbar(self)
        self.download_button = QPushButton("Download")
        # self.merge_button = QPushButton("Merge video and audio")
        # self.merge_button.setEnabled(False)
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.setLayout(self.__layout)
        #
        self.setUI()

    def setUI(self):
        self.add_search()
        #
        self.__layout.addWidget(self.bilibili_video_combobox)
        #
        self.__layout.addWidget(self.bilibili_progress_bar)
        #
        self.__layout.addWidget(self.download_button)
        self.handle_bilibili_download_button()
        # self.__layout.addWidget(self.merge_button)
        # self.merge_button.clicked.connect(
        #     self.merge_video_and_audio
        # )
        #
        self.__layout.addWidget(self.text)

    def add_search(self):
        search_bar_box = QHBoxLayout()
        search_bar_box.setSpacing(2)
        search_bar_box.setContentsMargins(0, 0, 0, 0)
        #
        self.bili_search_line.setPlaceholderText('输入 Bilibili 视频链接')
        self.bili_search_line.setMaxLength(100)
        self.bili_search_line.setValidator(self.regex_validator)
        #
        self.bili_search_button.clicked.connect(
            self.parse_bilibili_link
        )
        #
        search_bar_box.addWidget(self.bili_search_line)
        search_bar_box.addWidget(self.bili_search_button)
        self.__layout.addLayout(search_bar_box)

    def handle_bilibili_download_button(self):
        self.download_button.clicked.connect(
            self.start_bilibili_download
        )

    def start_bilibili_download(self):
        chosen_quality = self.bilibili_video_combobox.currentText()
        if not chosen_quality:
            self.bilibili_messages("Video quality is invalid")
            return
        self.download_button.setEnabled(False)
        #
        should_download_video = self.bilibili_video_urls[int(chosen_quality)][0]['url']
        should_download_audio = self.bilibili_audio_urls[0]['url']
        print(should_download_audio)
        #
        print(should_download_video)
        # print(chosen_quality)
        self.bilibili_messages('开始下载')
        # video initial
        content_length = self.get_content_length(should_download_video)
        fragments = self.split_by_chunk_size(content_length)
        arguments_for_threadPool = []
        for index, item in enumerate(fragments):
            own_header = deepcopy(self.origin_headers)
            own_header['range'] = item
            arguments_for_threadPool.append({
                'base_url': should_download_video,
                'headers': own_header,
                'count': index + 1
            })
        self.video_length = len(arguments_for_threadPool)
        self.bilibili_messages(f'video 长度为 {self.video_length}')
        # audio initial
        audio_content_length = self.get_content_length(should_download_audio)
        audio_fragments = self.split_by_chunk_size(audio_content_length)
        audio_arguments_for_threadpool = []
        for index, item in enumerate(audio_fragments):
            own_header = deepcopy(self.origin_headers)
            own_header['range'] = item
            audio_arguments_for_threadpool.append({
                'base_url': should_download_audio,
                'headers': own_header,
                'count': index + 1
            })
        self.audio_length = len(audio_arguments_for_threadpool)
        self.bilibili_messages(f'audio 长度为 {self.audio_length}')

        # set progress bar
        all_length = self.audio_length + self.video_length
        self.bilibili_progress_bar.setMinimum(1)
        self.bilibili_progress_bar.setValue(1)
        self.bilibili_progress_bar.setMaximum(all_length)
        # video download
        for argument in arguments_for_threadPool:
            video_worker = DownloadBiliBiliVideoRunnable(argument)
            video_worker.video_signal.connect_to_content_signal.connect(
                self.update_video_content
            )
            video_worker.video_signal.connect_to_main_message.connect(
                self.bilibili_messages
            )
            video_worker.video_signal.finished.connect(
                self.set_progress_bar_value
            )
            self.video_threadpool.start(video_worker)
        # audio download
        for argument in audio_arguments_for_threadpool:
            audio_worker = DownloadBiliBiliAudioRunnable(argument)
            audio_worker.audio_signal.connect_to_content_signal.connect(
                self.update_audio_content
            )
            audio_worker.audio_signal.connect_to_main_message.connect(
                self.bilibili_messages
            )
            audio_worker.audio_signal.finished.connect(
                self.set_progress_bar_value
            )
            self.audio_threadpool.start(audio_worker)

    def bilibili_messages(self, s):
        self.text.appendPlainText(s)

    def parse_bilibili_link(self):
        bilibili_video_url = self.bili_search_line.text()
        self.set_title_and_mkdir(
            bilibili_video_url.strip('/').split('/')[-1]
        )
        if not bilibili_video_url:
            self.bilibili_messages('Invalid video url')
            return
        self.bilibili_messages('开始解析')
        self.bilibili_messages(f'开始解析的 video 是 {bilibili_video_url}')
        bilibili_parse_thread = BilibiliParseThread(vu=bilibili_video_url, parent=self)
        bilibili_parse_thread.started.connect(
            self.start_parse_bilibili
        )
        bilibili_parse_thread.bilibili_video_urls_signal.connect(
            self.set_bilibili_video_urls
        )
        bilibili_parse_thread.bilibili_audio_urls_signal.connect(
            self.set_bilibili_audio_urls
        )
        bilibili_parse_thread.finished.connect(
            self.finish_parse_bilibili
        )
        bilibili_parse_thread.start()

    def set_bilibili_video_urls(self, video_urls_):
        self.bilibili_video_urls = video_urls_
        print(self.bilibili_video_urls)

    def set_bilibili_audio_urls(self, audio_urls_):
        self.bilibili_audio_urls = audio_urls_
        print(self.bilibili_audio_urls)

    def start_parse_bilibili(self):
        self.bilibili_messages('开始解析')
        self.bilibili_video_combobox.clear()
        self.bili_search_button.setText('解析中')
        self.bili_search_button.setEnabled(False)

    def finish_parse_bilibili(self):
        self.bilibili_messages('解析完成')
        qualities = self.bilibili_video_urls.keys()
        self.bilibili_add_video(qualities)
        self.bili_search_button.setText('开始解析')
        self.bili_search_button.setEnabled(True)

    def bilibili_add_video(self, video_qualities):
        for video_quality in video_qualities:
            self.bilibili_video_combobox.addItem(f'{video_quality}')

    def set_title_and_mkdir(self, title_):
        self.title = title_
        title_path = os.path.join(self.app_path, 'Result', title_)
        if not os.path.exists(title_path):
            os.makedirs(title_path)
        self.video_path = os.path.join(title_path, 'video.mp4')
        self.audio_path = os.path.join(title_path, 'audio.mp4')

    def concat_video(self):
        self.bilibili_messages('下载完成，开始合成为一个视频')
        video_length = len(self.video_contents)
        with open(self.video_path, 'wb') as f:
            for i in range(video_length):
                f.write(
                    self.video_contents[i + 1]
                )
        self.bilibili_messages('视频合成完成')

    def concat_audio(self):
        self.bilibili_messages('下载完成，开始合成为一个音频')
        audio_length = len(self.audio_contents)
        with open(self.audio_path, 'wb') as f:
            for i in range(audio_length):
                f.write(
                    self.audio_contents[i + 1]
                )
        self.bilibili_messages('音频合成完成')

    def update_video_content(self, part_video_content):
        self.video_contents.update(part_video_content)
        if self.video_length == len(self.video_contents):
            self.bilibili_messages('视频下载完成')
            self.concat_video()

    def update_audio_content(self, part_audio_content):
        self.audio_contents.update(part_audio_content)
        if self.audio_length == len(self.audio_contents):
            self.bilibili_messages('音频下载完成')
            self.concat_audio()

    def split_by_chunk_size(self, all_length):
        result = []
        start = 0
        end = start + self.chunk_size
        while end < all_length:
            result.append(
                f'bytes={start}-{end}'
            )
            start += self.chunk_size + 1
            end = start + self.chunk_size
        else:
            result.append(f'bytes={start}-{all_length - 1}')
        return result

    def get_content_length(self, url_):
        own_header = deepcopy(self.origin_headers)
        own_header['range'] = 'bytes=0-10'
        response = requests.get(
            url_,
            headers=own_header
        )
        resp_headers = response.headers
        content_length = int(
            resp_headers['Content-Range'].split('/')[1]
        )
        # self.bilibili_messages(f'长度为 {content_length}')
        return content_length

    def merge_video_and_audio(self):
        if self.video_path is None or not os.path.isfile(self.video_path):
            self.bilibili_messages(f'video {{{self.video_path}}} path is invalid')
            return
        if self.audio_path is None or not os.path.isfile(self.audio_path):
            self.bilibili_messages(f'audio {{{self.audio_length}}} path is invalid')
        if self.p is None:
            self.p = QProcess()
            self.bilibili_messages(f'Operation path is {self.video_path} and {self.audio_path}')
            self.p.readyReadStandardOutput.connect(
                self.handle_output
            )
            self.p.readyReadStandardError.connect(
                self.handle_error
            )
            self.p.finished.connect(
                self.process_finished
            )
            result_video_and_audio_path = os.path.join(
                os.path.dirname(self.video_path), 'result.mp4'
            )
            self.p.start('ffmpeg', ['-i', f'{self.video_path}', '-i', f'{self.audio_path}', '-threads', '20',
                                    f'{result_video_and_audio_path}'])

    def process_finished(self):
        self.bilibili_messages("Process finished")
        self.p = None
        self.bilibili_messages("音视频拼接完成")
        self.reset()

    def handle_output(self):
        data = self.p.readAllStandardOutput()
        self.bilibili_messages('a' + bytes(data).decode('utf8').strip())

    def handle_error(self):
        data = self.p.readAllStandardError()
        self.bilibili_messages(bytes(data).decode('utf8').strip())

    def active_or_not_down(self):
        if self.audio_threadpool.activeThreadCount() == 0 \
                and self.video_threadpool.activeThreadCount() == 0:
            self.download_button.setEnabled(True)
            self.reset()

    def reset(self):
        # clear variable
        self.bilibili_video_combobox.clear()
        self.audio_contents.clear()
        self.video_contents.clear()
        self.bilibili_video_urls.clear()
        self.bilibili_audio_urls.clear()
        self.audio_path = None
        self.video_path = None
        self.video_length = 0
        self.audio_length = 0
        self.bili_search_line.setText('')
        self.bilibili_progress_bar.setValue(1)
        self.download_button.setEnabled(True)
        self.title = 'UnKnow-bilibili'

    def set_progress_bar_value(self):
        old_value = self.bilibili_progress_bar.value()
        if old_value == self.bilibili_progress_bar.maximum():
            self.bilibili_messages('视频和音频单独下载完成')
            self.merge_video_and_audio()
        self.bilibili_progress_bar.setValue(old_value + 1)
