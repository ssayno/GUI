from PyQt6.QtCore import QThread, pyqtSignal
import requests
from copy import deepcopy


class InitialDownload(QThread):
    def __init__(self, url, parent=None):
        super().__init__(parent=parent)
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
        self.url = url
        self.chunk_size = 100000

    def run(self) -> None:
        content_length = self.get_content_length(self.url)
        fragments = self.split_by_chunk_size(content_length)
        arguments_for_threadPool = []
        for index, item in enumerate(fragments):
            own_header = deepcopy(self.origin_headers)
            own_header['range'] = item
            arguments_for_threadPool.append({
                'base_url': self.url,
                'headers': own_header,
                'count': index + 1
            })
        content_length = len(arguments_for_threadPool)
        # self.bilibili_messages(f'video 长度为 {self.video_length}')
        for argument in arguments_for_threadPool:
            video_worker = DownloadBiliBiliVideoRunnable(argument)
            video_worker.video_signal.connect_to_content_signal.connect(
                self.update_video_content
            )
            video_worker.video_signal.connect_to_main_message.connect(
                self.bilibili_messages
            )
            self.video_threadpool.start(video_worker)

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

