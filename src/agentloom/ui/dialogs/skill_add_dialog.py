from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from agentloom.config.loader import save_skill_entry
from agentloom.paths import config_dir
from agentloom.skills.skill_import import import_skills_from_input


class SkillAddDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config_root = config_dir()
        self.setWindowTitle("添加技能")
        self.setMinimumWidth(520)
        hint = QLabel(
            "安装为**应用级（全局）**技能，写入 data/skills_install/，所有任务中的 Agent 均可使用。\n"
            "任务专属技能由 find-skills 在安装根下当前任务目录的 .agentloom/skills/ 安装。\n"
            "支持本地路径或 GitHub tree 链接。示例：https://github.com/anthropics/skills/tree/main/skills"
        )
        hint.setWordWrap(True)
        self._input = QPlainTextEdit(self)
        self._input.setPlaceholderText(
            "D:\\skills\\my-skill\n或\nhttps://github.com/owner/repo/tree/main/path/to/folder"
        )
        self._input.setMaximumBlockCount(5)
        form = QFormLayout()
        form.addRow("路径 / URL", self._input)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        outer = QVBoxLayout(self)
        outer.addWidget(hint)
        outer.addLayout(form)
        outer.addWidget(buttons)

    def _on_ok(self) -> None:
        text = self._input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "校验失败", "请输入路径或 URL")
            return
        try:
            entries = import_skills_from_input(text, config_root=self._config_root)
        except (OSError, ValueError) as e:
            QMessageBox.warning(self, "导入失败", str(e))
            return
        except Exception as e:
            QMessageBox.warning(self, "导入失败", str(e))
            return
        for ent in entries:
            save_skill_entry(ent, self._config_root)
        QMessageBox.information(
            self,
            "完成",
            f"已添加 {len(entries)} 个技能：{', '.join(e.id for e in entries)}",
        )
        self.accept()
