from PyQt6.QtCore import (
    pyqtSignal, QRunnable, pyqtSlot, QObject
)
import requests


class VideoOrAudioSignal(QObject):
    connect_to_content_signal = pyqtSignal(dict)
    connect_to_main_message = pyqtSignal(str)
    finished = pyqtSignal()


class DownloadBiliBiliVideoRunnable(QRunnable):

    def __init__(self, argument):
        super().__init__()
        self.argument = argument
        self.retry_count = 0
        self.video_signal = VideoOrAudioSignal()

    @pyqtSlot()
    def run(self) -> None:
        flag = True
        base_url = self.argument['base_url']
        headers_ = self.argument['headers']
        count = self.argument['count']
        while True:
            try:
                resp = requests.get(base_url, headers=headers_)
                status_code, resp_content = resp.status_code, resp.content
                if status_code != 206:
                    print(status_code)
                    raise Exception
                else:
                    if not flag:
                        self.video_signal.connect_to_main_message.emit(f'video {count} 在 {self.retry_count} 次后成功')
                    # self.video_signal.connect_to_main_message.emit(f"{count} normal")
                    self.video_signal.connect_to_content_signal.emit({count: resp_content})
                    break
            except Exception as e:
                flag = False
                # self.video_signal.connect_to_main_message.emit(f'{count} : {e}')
            finally:
                self.retry_count += 1
        self.video_signal.finished.emit()


class DownloadBiliBiliAudioRunnable(QRunnable):

    def __init__(self, argument):
        super().__init__()
        self.argument = argument
        self.retry_count = 0
        self.audio_signal = VideoOrAudioSignal()

    @pyqtSlot()
    def run(self) -> None:
        flag = True
        base_url = self.argument['base_url']
        headers_ = self.argument['headers']
        count = self.argument['count']
        while True:
            try:
                resp = requests.get(base_url, headers=headers_)
                status_code, resp_content = resp.status_code, resp.content
                if status_code != 206:
                    print(status_code)
                    raise Exception
                else:
                    if not flag:
                        self.audio_signal.connect_to_main_message.emit(f'audio {count} 在 {self.retry_count} 次后成功')
                    self.audio_signal.connect_to_content_signal.emit({count: resp_content})
                    break
            except Exception as e:
                flag = False
                # self.audio_signal.connect_to_main_message.emit(f'{count} : {e}')
            finally:
                self.retry_count += 1
        self.audio_signal.finished.emit()

