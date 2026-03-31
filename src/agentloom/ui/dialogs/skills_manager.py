from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from agentloom.config.builtin_skills import ensure_builtin_skill_configs
from agentloom.config.loader import delete_skill_entry, load_all, save_skill_entry
from agentloom.config.skill_markdown import resolve_skill_row
from agentloom.paths import config_dir, install_root
from agentloom.ui.dialogs.skill_add_dialog import SkillAddDialog


class SkillsManagerDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config_root = config_dir()
        self._install_root = install_root()
        self.setWindowTitle("技能管理（应用级 / 全局）")
        self.setMinimumSize(760, 400)
        self._table = QTableWidget(self)
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["启用", "技能名称", "描述", "目录"]
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.itemChanged.connect(self._on_item_changed)
        btn_add = QPushButton("添加…", self)
        btn_del = QPushButton("删除", self)
        btn_refresh = QPushButton("刷新", self)
        btn_close = QPushButton("关闭", self)
        btn_add.clicked.connect(self._on_add)
        btn_del.clicked.connect(self._on_delete)
        btn_refresh.clicked.connect(lambda: self._refresh())
        btn_close.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addWidget(btn_add)
        row.addWidget(btn_del)
        row.addWidget(btn_refresh)
        row.addStretch()
        row.addWidget(btn_close)
        outer = QVBoxLayout(self)
        outer.addWidget(self._table)
        outer.addLayout(row)
        self._refresh(silent=True)

    def _refresh(self, *, silent: bool = False) -> None:
        ensure_builtin_skill_configs()
        self._table.blockSignals(True)
        self._table.setRowCount(0)
        try:
            cfg = load_all(self._config_root)
        except Exception as e:
            self._table.blockSignals(False)
            if not silent:
                QMessageBox.warning(self, "加载失败", str(e))
            return
        for ent in cfg.skills:
            _, name, desc, sd = resolve_skill_row(self._install_root, ent)
            r = self._table.rowCount()
            self._table.insertRow(r)
            chk = QTableWidgetItem()
            chk.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            chk.setCheckState(
                Qt.CheckState.Checked if ent.enabled else Qt.CheckState.Unchecked
            )
            chk.setData(Qt.ItemDataRole.UserRole, ent.id)
            self._table.setItem(r, 0, chk)
            self._table.setItem(r, 1, QTableWidgetItem(name))
            self._table.setItem(r, 2, QTableWidgetItem(desc))
            self._table.setItem(r, 3, QTableWidgetItem(sd))
        self._table.blockSignals(False)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() != 0:
            return
        sid = item.data(Qt.ItemDataRole.UserRole)
        if not sid:
            return
        cfg = load_all(self._config_root)
        ent = next((x for x in cfg.skills if x.id == sid), None)
        if not ent:
            return
        enabled = item.checkState() == Qt.CheckState.Checked
        if ent.enabled == enabled:
            return
        try:
            save_skill_entry(ent.model_copy(update={"enabled": enabled}), self._config_root)
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))
            self._refresh(silent=True)

    def _selected_skill_id(self) -> str | None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        r = rows[0].row()
        it = self._table.item(r, 0)
        if not it:
            return None
        return it.data(Qt.ItemDataRole.UserRole)

    def _on_add(self) -> None:
        dlg = SkillAddDialog(parent=self)
        if dlg.exec():
            self._refresh(silent=True)

    def _on_delete(self) -> None:
        sid = self._selected_skill_id()
        if not sid:
            QMessageBox.information(self, "提示", "请先选择一行")
            return
        r = QMessageBox.question(
            self,
            "确认删除",
            f"删除技能「{sid}」？（通过客户端安装到 data/skills_install 的会一并删除文件）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if r != QMessageBox.StandardButton.Yes:
            return
        delete_skill_entry(
            sid,
            self._config_root,
            install_root_for_payload=self._install_root,
        )
        self._refresh(silent=True)
