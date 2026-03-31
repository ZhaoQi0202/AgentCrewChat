from pathlib import Path

from pydantic import ValidationError
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from agentloom.config.llm_settings_store import load_llm_settings, save_llm_settings
from agentloom.config.models import LlmSettings


class ModelSettingsDialog(QDialog):
    def __init__(self, install_root: Path | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._install_root = install_root
        self.setWindowTitle("模型设置")
        self._provider = QComboBox(self)
        self._provider.addItems(["openai", "anthropic"])
        self._openai_key = QLineEdit(self)
        self._openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._anthropic_key = QLineEdit(self)
        self._anthropic_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._openai_model = QLineEdit(self)
        self._anthropic_model = QLineEdit(self)
        self._show_keys = QCheckBox("显示密钥", self)
        self._show_keys.toggled.connect(self._on_show_keys)
        form = QFormLayout()
        form.addRow("默认提供商", self._provider)
        form.addRow("OpenAI API Key", self._openai_key)
        form.addRow("OpenAI 模型", self._openai_model)
        form.addRow("Anthropic API Key", self._anthropic_key)
        form.addRow("Anthropic 模型", self._anthropic_model)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        outer = QVBoxLayout(self)
        outer.addLayout(form)
        outer.addWidget(self._show_keys)
        outer.addWidget(buttons)
        self._load()

    def _on_show_keys(self, checked: bool) -> None:
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self._openai_key.setEchoMode(mode)
        self._anthropic_key.setEchoMode(mode)

    def _load(self) -> None:
        try:
            s = load_llm_settings(self._install_root)
        except Exception as e:
            QMessageBox.warning(self, "读取失败", str(e))
            s = LlmSettings()
        idx = self._provider.findText(s.default_provider)
        self._provider.setCurrentIndex(max(0, idx))
        self._openai_key.setText(s.openai_api_key)
        self._anthropic_key.setText(s.anthropic_api_key)
        self._openai_model.setText(s.openai_model)
        self._anthropic_model.setText(s.anthropic_model)

    def _on_save(self) -> None:
        prov = self._provider.currentText().strip()
        if prov not in ("openai", "anthropic"):
            QMessageBox.warning(self, "校验失败", "提供商无效")
            return
        try:
            settings = LlmSettings(
                default_provider=prov,
                openai_api_key=self._openai_key.text().strip(),
                anthropic_api_key=self._anthropic_key.text().strip(),
                openai_model=self._openai_model.text().strip() or "gpt-4o-mini",
                anthropic_model=self._anthropic_model.text().strip() or "claude-sonnet-4-20250514",
            )
        except ValidationError as e:
            QMessageBox.warning(self, "校验失败", str(e))
            return
        try:
            save_llm_settings(settings, self._install_root)
        except OSError as e:
            QMessageBox.warning(self, "保存失败", str(e))
            return
        self.accept()
