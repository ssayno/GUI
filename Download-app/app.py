import sys
from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QTabWidget
)
from components.youtube.youtube_widget import YoutubeWidget
from components.bilibili.bilibili_widget import BilibiliWidget


class Downloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(900, 500)
        # set center widget
        self.cw = QTabWidget(parent=self)
        self.setCentralWidget(self.cw)
        #
        self.add_youtube_downloader()

    def add_youtube_downloader(self):
        youtube_downloader = YoutubeWidget(parent=self)
        bilibili_downloader = BilibiliWidget(parent=self)
        self.cw.addTab(youtube_downloader, 'YouTube')
        self.cw.addTab(bilibili_downloader, 'BiliBili')
        self.cw.setCurrentWidget(bilibili_downloader)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    downloader = Downloader()
    downloader.show()
    sys.exit(app.exec())
