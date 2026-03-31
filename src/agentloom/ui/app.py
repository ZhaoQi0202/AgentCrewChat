from PySide6.QtWidgets import QApplication, QMessageBox

from agentloom.bootstrap import check_writable_root
from agentloom.ui.main_window import MainWindow


def run_app() -> int:
    app = QApplication([])
    if not check_writable_root():
        QMessageBox.warning(
            None,
            "AgentLoom",
            "安装目录不可写，请将程序放在可写目录后重试。",
        )
        return 1
    win = MainWindow()
    win.show()
    return app.exec()
