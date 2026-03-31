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

from agentloom.config.model_connection_store import (
    allocate_connection_id,
    list_model_connections,
    save_model_connection_entry,
)
from agentloom.config.models import ModelConnectionEntry


class ModelConnectionEditorDialog(QDialog):
    def __init__(
        self,
        *,
        install_root: Path | None = None,
        entry: ModelConnectionEntry | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._install_root = install_root
        self._existing_id = entry.id if entry else None
        self.setWindowTitle("编辑连接" if entry else "新建连接")
        self._name = QLineEdit(self)
        self._provider = QComboBox(self)
        self._provider.addItem("OpenAI 兼容", "openai_compatible")
        self._provider.addItem("Anthropic", "anthropic")
        self._base_url = QLineEdit(self)
        self._base_url.setPlaceholderText("留空则使用官方默认地址")
        self._api_key = QLineEdit(self)
        self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._model = QLineEdit(self)
        self._enabled = QCheckBox("启用", self)
        self._enabled.setChecked(True)
        form = QFormLayout()
        form.addRow("显示名称", self._name)
        form.addRow("提供商", self._provider)
        form.addRow("Base URL", self._base_url)
        form.addRow("API Key", self._api_key)
        form.addRow("模型 ID", self._model)
        form.addRow("", self._enabled)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        outer = QVBoxLayout(self)
        outer.addLayout(form)
        outer.addWidget(buttons)
        if entry:
            self._name.setText(entry.name or entry.id)
            idx = self._provider.findData(entry.provider)
            self._provider.setCurrentIndex(max(0, idx))
            self._base_url.setText(entry.base_url)
            self._api_key.setText(entry.api_key)
            self._model.setText(entry.model)
            self._enabled.setChecked(entry.enabled)

    def _on_save(self) -> None:
        name = self._name.text().strip()
        if not name:
            QMessageBox.warning(self, "校验失败", "显示名称不能为空")
            return
        model = self._model.text().strip()
        if not model:
            QMessageBox.warning(self, "校验失败", "模型 ID 不能为空")
            return
        prov = self._provider.currentData()
        if prov not in ("openai_compatible", "anthropic"):
            QMessageBox.warning(self, "校验失败", "提供商无效")
            return
        existing = {e.id for e in list_model_connections(self._config_root())}
        if self._existing_id:
            cid = self._existing_id
        else:
            cid = allocate_connection_id(name, existing)
        try:
            entry = ModelConnectionEntry(
                id=cid,
                name=name,
                provider=prov,
                base_url=self._base_url.text().strip(),
                api_key=self._api_key.text().strip(),
                model=model,
                enabled=self._enabled.isChecked(),
            )
        except ValidationError as e:
            QMessageBox.warning(self, "校验失败", str(e))
            return
        try:
            save_model_connection_entry(entry, config_root=self._config_root())
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))
            return
        self.accept()

    def _config_root(self) -> Path | None:
        if self._install_root is None:
            return None
        return self._install_root / "config"
