from PySide6.QtWidgets import QApplication

from agentloom.ui.main_window import MainWindow


def run_app() -> int:
    app = QApplication([])
    win = MainWindow()
    win.show()
    return app.exec()
