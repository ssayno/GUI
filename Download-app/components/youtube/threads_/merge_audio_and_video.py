from PyQt6.QtCore import QThread, QProcess, pyqtSignal
import subprocess


class MergeAudioAndVideo(QThread):
    message_signal = pyqtSignal(str)

    def __init__(self, video_path, audio_path, parent=None):
        super().__init__(parent=parent)
        self.vp = video_path
        self.ap = audio_path
        self.p = QProcess()

    def run(self) -> None:
        # subprocess.run(f'ffmpeg -i {self.vp} -i {self.ap} result.mp4', shell=True)
        self.p.readyReadStandardOutput.connect(
            self.handle_output
        )
        self.p.readyReadStandardError.connect(
            self.handle_error
        )
        self.p.finished.connect(
            self.process_finished
        )
        self.p.start('ffmpeg', ['-i', f'{self.vp}', '-i', f'{self.ap}', 'result.mp4'])

    def messages(self, s):
        self.message_signal.emit(s)

    def process_finished(self):
        self.messages("Process finished")
        self.p = None

    def handle_output(self):
        data = self.p.readAllStandardOutput()
        self.messages(bytes(data).decode('utf8').strip())

    def handle_error(self):
        data = self.p.readAllStandardError()
        self.messages(bytes(data).decode('utf8').strip())
