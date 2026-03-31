from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QSplitter, QWidget

from agentloom.paths import install_root
from agentloom.ui.panels.activity_panel import ActivityPanel
from agentloom.ui.panels.chat_panel import ChatPanel
from agentloom.ui.panels.task_list import TaskListPanel


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"AgentLoom — {install_root()}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self._task_list = TaskListPanel()
        self._chat = ChatPanel()
        self._activity = ActivityPanel()
        splitter.addWidget(self._task_list)
        splitter.addWidget(self._chat)
        splitter.addWidget(self._activity)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)
        layout.addWidget(splitter)
        self._chat.message_sent.connect(self._activity.append_line)
