import os
from PyQt6.QtCore import pyqtSignal, QThread
import threading
import requests

VIDEO_SEMAPHORE = threading.Semaphore(40)
AUDIO_SEMAPHORE = threading.Semaphore(40)


class DownloadVideo(QThread):
    video_signal = pyqtSignal(dict)

    def __init__(self, vp, count, url_, parent=None):
        super().__init__(parent=parent)
        self.count = count
        self.__url = url_
        self.limit = 5
        self.video_path = vp
        if not os.path.exists(self.video_path):
            os.mkdir(self.video_path)

    def run(self) -> None:
        VIDEO_SEMAPHORE.acquire()
        self.retry()
        VIDEO_SEMAPHORE.release()

    def retry(self, retry_=False):
        try:
            video_file = os.path.join(self.video_path, f'{self.count}.mp4')
            with open(video_file, 'wb') as f:
                resp = requests.post(self.__url)
                resp_status_code = resp.status_code
                if resp_status_code == 200:
                    f.write(resp.content)
                else:
                    print(f'{self.count} 状态码为 {resp_status_code}')
                    raise Exception
            if retry_:
                print(f'{self.count} video {self.limit} 次 尝试成功')
        except Exception as e:
            print(f'{self.count} 失败')
            if self.limit == 0:
                print(f'video {self.count} 尝试 5 次依旧失败')
                return
            self.limit -= 1
            self.retry(retry_=True)


class DownloadAudio(QThread):
    audio_signal = pyqtSignal(dict)

    def __init__(self, ap, count, url_, parent=None):
        super().__init__(parent=parent)
        self.count = count
        self.__url = url_
        self.limit = 5
        self.audio_path = ap
        if not os.path.exists(self.audio_path):
            os.mkdir(self.audio_path)

    def run(self) -> None:
        AUDIO_SEMAPHORE.acquire()
        self.retry()
        AUDIO_SEMAPHORE.release()

    def retry(self, retry_=False):
        # print(self.__url)
        try:
            audio_file = os.path.join(self.audio_path, f'{self.count}.mp4')
            with open(audio_file, 'wb') as f:
                resp = requests.post(self.__url)
                resp_status_code = resp.status_code
                if resp_status_code == 200:
                    f.write(resp.content)
                else:
                    print(f'{self.count} 状态码为 {resp_status_code}')
                    raise Exception
            if retry_:
                print(f'audio {self.count} 尝试成功')
        except Exception as e:
            print(f'audio {self.count} 失败')
            if self.limit == 0:
                print(f'audio 尝试 5 次依旧失败')
                return
            self.limit -= 1
            self.retry(retry_=True)
