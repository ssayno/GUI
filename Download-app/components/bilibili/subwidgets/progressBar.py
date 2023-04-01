from PyQt6.QtCore import QPropertyAnimation, QTimer, Qt
from PyQt6.QtWidgets import QProgressBar, QStyleFactory


class OwnProgressbar(QProgressBar):
    def __init__(self, parent) -> None:
        super(OwnProgressbar, self).__init__(parent=parent)
        # for Mac, you should add this to show percentage
        self.setStyle(QStyleFactory.create('Fusion'))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFormat('Downloading... %p%')
        self.setRange(0, 100)
        # create animation
        self.create_animation()
        # set a status
        self.allow_next = True
        self.setOrientation(Qt.Orientation.Horizontal)
        # self.setOrientation(Qt.Vertical)
        self.valueChanged.connect(self.value_change)

    def setValue(self, value: int) -> None:
        self.old_value = self.value()
        return super().setValue(value)
    #
    # def set_value(self):
    #     if self.allow_next:
    #         self.reset()
    #         self.allow_next = False
    #         for i in range(0, 101):
    #             QTimer.singleShot(20 * i, lambda x=i: self.setValue(x))

    def value_change(self, _value):
        #if self.isMaximized(): isMaximized not useful
        if _value == self.maximum():
            self.allow_next = True
        else:
            self._animation.start()

    def create_animation(self):
        if not hasattr(self, "old_value"):
            self.old_value = self.value()
        self._animation = QPropertyAnimation(self, b'value', self.parent())
        self._animation.setStartValue(self.value())
        self._animation.setEndValue(self.old_value)