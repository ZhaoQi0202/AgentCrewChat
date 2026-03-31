from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from agentloom import bootstrap
from agentloom.tasks import workspace


class TaskListPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        bootstrap.ensure_layout()
        self._list = QListWidget()
        btn = QPushButton("新建任务")
        btn.clicked.connect(self._on_new_task)
        layout = QVBoxLayout(self)
        layout.addWidget(self._list)
        row = QHBoxLayout()
        row.addWidget(btn)
        layout.addLayout(row)
        self.refresh()

    def refresh(self) -> None:
        self._list.clear()
        bootstrap.ensure_layout()
        for p in workspace.list_tasks():
            self._list.addItem(QListWidgetItem(str(p)))

    def _on_new_task(self) -> None:
        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "新建任务", "任务名称:")
        if not ok or not name.strip():
            return
        try:
            workspace.create_task(name.strip())
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
            return
        self.refresh()
