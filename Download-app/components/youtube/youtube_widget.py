import os
from PyQt6.QtWidgets import (
    QWidget, QLineEdit, QVBoxLayout, QComboBox, QPushButton, QHBoxLayout, QPlainTextEdit
)
from PyQt6.QtGui import (
    QRegularExpressionValidator
)
from PyQt6.QtCore import Qt, QThreadPool
from .subwidgets.progressBar import OwnProgressbar
from .threads_.parse_thread import ThreadParseQuality
from .threads_.download_thread import DownloadVideoOrAudioRunnable
from PyQt6.QtCore import QRegularExpression, QProcess


class YoutubeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        current_path = os.path.dirname(__file__)
        with open(os.path.join(current_path, 'youtube.css'), 'r') as f:
            self.setStyleSheet(f.read())
        # chunk size
        self.chunk_size = 100000
        #
        self.p = None
        self.video_threadPools = QThreadPool()
        self.video_threadPools.setMaxThreadCount(100)
        self.audio_threadPool = QThreadPool()
        self.audio_threadPool.setMaxThreadCount(60)
        #
        self.video_contents = {}
        self.audio_contents = {}
        self.video_urls = []
        self.audio_urls = []
        self.title = "UnKnow"
        #
        self.regex_validator = QRegularExpressionValidator(
            QRegularExpression(
                '^https://www.youtube.com/watch[?]v=[a-zA-Z0-9-_]+'
            )
        )
        #
        self.__layout = QVBoxLayout()
        self.__layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        #
        self.search_line = QLineEdit()
        self.search_line.setObjectName('searchLine')
        self.search_button = QPushButton("开始解析")
        self.search_button.setObjectName('searchButton')
        self.video_combobox = QComboBox()
        self.youtube_progress_bar = OwnProgressbar(parent=self)
        self.download_button = QPushButton("Download")
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.setLayout(self.__layout)
        self.setUI()

    def setUI(self):
        self.add_search()
        #
        self.__layout.addWidget(self.video_combobox)
        #
        self.__layout.addWidget(self.youtube_progress_bar)
        #
        self.__layout.addWidget(self.download_button)
        self.handle_download_button()
        #
        self.__layout.addWidget(self.text)

    def add_search(self):
        search_bar_box = QHBoxLayout()
        search_bar_box.setSpacing(2)
        search_bar_box.setContentsMargins(0, 0, 0, 0)
        #
        self.search_line.setPlaceholderText('输入 YouTube 视频链接')
        self.search_line.setMaxLength(100)
        self.search_line.setValidator(self.regex_validator)
        search_bar_box.addWidget(self.search_line)
        #
        self.search_button.clicked.connect(
            lambda: self.parse_youtube_link(self.search_line.text())
        )
        search_bar_box.addWidget(self.search_button)
        #
        self.__layout.addLayout(search_bar_box)

    def add_video(self, video_qualities):
        for video_quality in video_qualities:
            self.video_combobox.addItem(video_quality)

    def handle_download_button(self):
        self.download_button.clicked.connect(
            self.start_download
        )

    def parse_youtube_link(self, video_url):
        if not video_url:
            return
        else:
            self.messages(f'现在解析的视频是 {video_url}')
            self.messages('开始解析')
        parse_thread = ThreadParseQuality(vu=video_url, parent=self)
        parse_thread.started.connect(
            self.start_parse_thread
        )
        parse_thread.video_urls_signal.connect(
            self.set_video_urls
        )
        parse_thread.audio_urls_signal.connect(
            self.set_audio_urls
        )
        parse_thread.title_signal.connect(
            self.set_title
        )
        parse_thread.finished.connect(
            self.finish_parse_thread
        )
        parse_thread.start()

    def set_video_urls(self, vu):
        self.video_urls = vu

    def set_audio_urls(self, au):
        self.audio_urls = au

    def set_title(self, title_):
        self.title = title_

    def start_parse_thread(self):
        self.video_combobox.clear()
        self.search_button.setText("解析中")
        self.search_button.setEnabled(False)

    def finish_parse_thread(self):
        self.messages('解析完成')
        qualities = self.video_urls.keys()
        self.add_video(qualities)
        self.search_button.setText('开始解析')
        self.search_button.setEnabled(True)

    def start_download(self):
        chosen_quality = self.video_combobox.currentText()
        if not chosen_quality:
            self.messages("Video quality is invalid")
            return
        self.messages("开始下载")
        self.download_button.setEnabled(False)
        # print(chosen_quality)
        should_download_video = self.video_urls[chosen_quality][0]
        # print(should_download_video)
        # 默认使用最高
        current_path = os.path.dirname(__file__)
        dir_path = os.path.join(current_path, "Result", self.title)
        video_path = os.path.join(dir_path, 'video')
        audio_path = os.path.join(dir_path, 'audio')
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=False)
        # print(video_path)
        video_url__ = should_download_video['url']
        video_length = should_download_video['length']
        # video
        video_result = self.split_by_chunk_size(int(video_length))
        range_video_length = len(video_result)
        # audio
        audio_url = self.audio_urls[0]['url']
        audio_length = self.audio_urls[0]['length']
        audio_result = self.split_by_chunk_size(int(audio_length))
        range_audio_length = len(audio_result)
        #
        range_length = range_video_length + range_audio_length
        self.youtube_progress_bar.setMinimum(1)
        self.youtube_progress_bar.setValue(1)
        self.youtube_progress_bar.setMaximum(range_length)
        # print(range_length)
        for index, item__ in enumerate(video_result):
            need_url = f'{video_url__}&{item__}'
            arguments = {
                "count": index + 1,
                "url": need_url
            }
            video_worker = DownloadVideoOrAudioRunnable(arguments=arguments)
            video_worker.signals.connect_content_signal.connect(
                self.add_to_video_contents
            )
            video_worker.signals.finished.connect(
                self.set_progress_bar_value
            )
            video_worker.signals.connect_message_signal.connect(
                self.messages
            )
            self.video_threadPools.start(video_worker)
        for index, item__ in enumerate(audio_result):
            need_url = f'{audio_url}&{item__}'
            arguments = {
                "count": index + 1,
                "url": need_url
            }
            audio_worker = DownloadVideoOrAudioRunnable(arguments=arguments)
            audio_worker.signals.connect_content_signal.connect(
                self.add_to_audio_contents
            )
            audio_worker.signals.finished.connect(
                self.set_progress_bar_value
            )
            audio_worker.signals.connect_message_signal.connect(
                self.messages
            )
            self.audio_threadPool.start(audio_worker)

    def set_progress_bar_value(self):
        old_value = self.youtube_progress_bar.value()
        if old_value == self.youtube_progress_bar.maximum():
            self.messages('视频和音频单独下载完成')
            self.concat_video_and_audio()
        self.youtube_progress_bar.setValue(old_value + 1)

    def split_by_chunk_size(self, all_length):
        result = []
        start = 0
        end = start + self.chunk_size
        while end < all_length:
            result.append(
                f'range={start}-{end}'
            )
            start += self.chunk_size + 1
            end = start + self.chunk_size
        else:
            result.append(f'range={start}-{all_length - 1}')
        return result

    def add_to_video_contents(self, single_video):
        self.video_contents.update(single_video)

    def add_to_audio_contents(self, single_audio):
        self.audio_contents.update(single_audio)

    def concat_video_and_audio(self):
        video_length = len(self.video_contents)
        audio_length = len(self.audio_contents)
        app_path = os.path.abspath('.')
        title_path = os.path.abspath(
            os.path.join(app_path, 'Result', self.title)
        )
        if not os.path.exists(title_path):
            os.makedirs(title_path)
        video_path = os.path.join(
            title_path, 'video.mp4'
        )
        audio_path = os.path.join(
            title_path, 'audio.mp4'
        )
        result_video_and_audio_path = os.path.join(
            title_path, f'{self.title}.mp4'
        )
        if os.path.exists(result_video_and_audio_path):
            print('exists')
        with open(video_path, 'wb') as f:
            for i in range(video_length):
                f.write(
                    self.video_contents[i + 1]
                )
        with open(audio_path, 'wb') as f:
            for i in range(audio_length):
                f.write(
                    self.audio_contents[i + 1]
                )
        self.messages("分别合成 video 和 audio 成功")
        if self.p is None:
            self.p = QProcess()
            self.messages(f'Operation path is {video_path} and {audio_path}')
            self.p.readyReadStandardOutput.connect(
                self.handle_output
            )
            self.p.readyReadStandardError.connect(
                self.handle_error
            )
            self.p.finished.connect(
                self.process_finished
            )
            self.p.start('ffmpeg', ['-i', f'{video_path}', '-i', f'{audio_path}', '-threads', '20',
                                    f'{result_video_and_audio_path}'])

    def messages(self, s):
        self.text.appendPlainText(s)

    def process_finished(self):
        self.messages("Process finished")
        self.p = None
        self.messages("音视频拼接完成")
        self.download_button.setEnabled(True)
        self.reset()

    def handle_output(self):
        data = self.p.readAllStandardOutput()
        self.messages(bytes(data).decode('utf8').strip())

    def handle_error(self):
        data = self.p.readAllStandardError()
        self.messages(bytes(data).decode('utf8').strip())

    def reset(self):
        # clear variable
        self.title = "UnKnow"
        self.video_urls.clear()
        self.audio_urls.clear()
        self.video_contents.clear()
        self.audio_contents.clear()
        self.video_combobox.clear()
        self.youtube_progress_bar.setValue(1)
        self.search_line.setText('')
