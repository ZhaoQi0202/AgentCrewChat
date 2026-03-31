from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget


class ChatPanel(QWidget):
    message_sent = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._edit = QPlainTextEdit()
        self._edit.setPlaceholderText("消息…")
        send = QPushButton("Send")
        send.clicked.connect(self._emit_send)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(send)
        layout = QVBoxLayout(self)
        layout.addWidget(self._edit)
        layout.addLayout(row)

    def _emit_send(self) -> None:
        text = self._edit.toPlainText().strip()
        if text:
            self.message_sent.emit(text)
