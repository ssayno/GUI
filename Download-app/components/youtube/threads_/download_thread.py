import os
from PyQt6.QtCore import pyqtSignal, QThread, QRunnable, pyqtSlot, QObject
import requests


class AudioOrVideoSignals(QObject):
    connect_content_signal = pyqtSignal(dict)
    connect_message_signal = pyqtSignal(str)
    finished = pyqtSignal()


class DownloadVideoOrAudioRunnable(QRunnable):
    def __init__(self, arguments):
        self.arguments = arguments
        self.signals = AudioOrVideoSignals()
        self.retry_count = 0
        super().__init__()

    @pyqtSlot()
    def run(self) -> None:
        count = self.arguments['count']
        url = self.arguments['url']
        flag = True
        while True:
            try:
                resp = requests.post(url)
                resp_status_code = resp.status_code
                if resp_status_code == 200:
                    if not flag:
                        self.signals.connect_message_signal.emit(f"{count} 在尝试 {self.retry_count} 次后成功")
                    self.signals.connect_content_signal.emit(
                        {count: resp.content}
                    )
                    break
                else:
                    raise Exception
            except Exception as e:
                flag = False
            finally:
                self.retry_count += 1
        self.signals.finished.emit()


# class DownloadAudioRunnable(QRunnable):
#     def __init__(self, argument):
#         self.argument = argument
#         self.audio_signal = AudioOrVideoSignals()
#         super().__init__()
#
#     @pyqtSlot()
#     def run(self) -> None:
#         count = self.argument['count']
#         url = self.argument['url']
#         while True:
#             try:
#                 resp = requests.post(url)
#                 resp_status_code = resp.status_code
#                 if resp_status_code == 200:
#                     self.audio_signal.connect_content_signal.emit(
#                         {count: resp.content}
#                     )
#                     break
#                 else:
#                     self.audio_signal.connect_message_signal.emit(f'{count} 状态码为 {resp_status_code}')
#                     raise Exception
#             except Exception as e:
#                 print(e)


# import threading
#
# VIDEO_SEMAPHORE = threading.Semaphore(40)
# AUDIO_SEMAPHORE = threading.Semaphore(40)
# class DownloadVideo(QThread):
#     video_signal = pyqtSignal(dict)
#
#     def __init__(self, vp, count, url_, parent=None):
#         super().__init__(parent=parent)
#         self.count = count
#         self.__url = url_
#         self.limit = 5
#         self.video_path = vp
#         if not os.path.exists(self.video_path):
#             os.mkdir(self.video_path)
#
#     def run(self) -> None:
#         VIDEO_SEMAPHORE.acquire()
#         self.retry()
#         VIDEO_SEMAPHORE.release()
#
#     def retry(self, retry_=False):
#         try:
#             video_file = os.path.join(self.video_path, f'{self.count}.mp4')
#             resp = requests.post(self.__url)
#             resp_status_code = resp.status_code
#             if resp_status_code == 200:
#                 self.video_signal.emit({
#                     self.count: resp.content
#                 })
#             else:
#                 print(f'{self.count} 状态码为 {resp_status_code}')
#                 raise Exception
#             if retry_:
#                 print(f'{self.count} video {self.limit} 次 尝试成功')
#         except Exception as e:
#             print(f'{self.count} 失败')
#             if self.limit == 0:
#                 print(f'video {self.count} 尝试 5 次依旧失败')
#                 return
#             self.limit -= 1
#             self.retry(retry_=True)
#
#
# class DownloadAudio(QThread):
#     audio_signal = pyqtSignal(dict)
#
#     def __init__(self, ap, count, url_, parent=None):
#         super().__init__(parent=parent)
#         self.count = count
#         self.__url = url_
#         self.limit = 5
#         self.audio_path = ap
#         if not os.path.exists(self.audio_path):
#             os.mkdir(self.audio_path)
#
#     def run(self) -> None:
#         AUDIO_SEMAPHORE.acquire()
#         self.retry()
#         AUDIO_SEMAPHORE.release()
#
#     def retry(self, retry_=False):
#         # print(self.__url)
#         try:
#             audio_file = os.path.join(self.audio_path, f'{self.count}.mp4')
#             resp = requests.post(self.__url)
#             resp_status_code = resp.status_code
#             if resp_status_code == 200:
#                 self.audio_signal.emit({
#                     self.count: resp.content
#                 })
#             else:
#                 print(f'{self.count} 状态码为 {resp_status_code}')
#                 raise Exception
#             if retry_:
#                 print(f'audio {self.count} 尝试成功')
#         except Exception as e:
#             print(f'audio {self.count} 失败')
#             if self.limit == 0:
#                 print(f'audio 尝试 5 次依旧失败')
#                 return
#             self.limit -= 1
#             self.retry(retry_=True)
