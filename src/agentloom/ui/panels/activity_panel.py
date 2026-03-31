from PySide6.QtWidgets import QListWidget, QVBoxLayout, QWidget


class ActivityPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._list = QListWidget()
        QVBoxLayout(self).addWidget(self._list)

    def append_line(self, line: str) -> None:
        self._list.addItem(line)
