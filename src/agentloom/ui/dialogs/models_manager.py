from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from agentloom.config.llm_settings_store import load_llm_settings, save_llm_settings
from agentloom.config.model_connection_store import (
    delete_model_connection_entry,
    list_model_connections,
    load_model_connection,
    save_model_connection_entry,
)
from agentloom.llm.connection_check import probe_model_connection
from agentloom.paths import config_dir
from agentloom.ui.dialogs.model_connection_editor import ModelConnectionEditorDialog


class _ConnectionTestThread(QThread):
    result = Signal(str, bool, str)

    def __init__(
        self,
        items: list[tuple[str, ModelConnectionEntry]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._items = items

    def run(self) -> None:
        for cid, ent in self._items:
            ok, msg = probe_model_connection(
                ent.provider, ent.base_url, ent.api_key, ent.model
            )
            self.result.emit(cid, ok, msg)


class ModelsManagerDialog(QDialog):
    def __init__(self, install_root: Path | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._install_root = install_root
        self._config_root = (
            (install_root / "config").resolve() if install_root is not None else config_dir()
        )
        self.setWindowTitle("模型管理")
        self.setMinimumSize(900, 420)
        self._status: dict[str, str] = {}
        self._test_thread: _ConnectionTestThread | None = None
        self._table = QTableWidget(self)
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["启用", "名称", "模型", "Base URL", "连接状态", "测试"]
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.itemChanged.connect(self._on_item_changed)
        self._default_combo = QComboBox(self)
        self._default_combo.currentIndexChanged.connect(self._on_default_changed)
        btn_new = QPushButton("新建连接", self)
        btn_edit = QPushButton("编辑", self)
        btn_del = QPushButton("删除", self)
        btn_test_sel = QPushButton("测试选中", self)
        btn_test_all = QPushButton("测试全部", self)
        btn_refresh = QPushButton("刷新", self)
        btn_close = QPushButton("关闭", self)
        btn_new.clicked.connect(self._on_new)
        btn_edit.clicked.connect(self._on_edit)
        btn_del.clicked.connect(self._on_delete)
        btn_test_sel.clicked.connect(self._on_test_selected)
        btn_test_all.clicked.connect(self._on_test_all)
        btn_refresh.clicked.connect(self._refresh)
        btn_close.clicked.connect(self.accept)
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("默认连接"))
        row1.addWidget(self._default_combo, 1)
        row2 = QHBoxLayout()
        row2.addWidget(btn_new)
        row2.addWidget(btn_edit)
        row2.addWidget(btn_del)
        row2.addWidget(btn_test_sel)
        row2.addWidget(btn_test_all)
        row2.addWidget(btn_refresh)
        row2.addStretch()
        row2.addWidget(btn_close)
        outer = QVBoxLayout(self)
        outer.addLayout(row1)
        outer.addWidget(self._table)
        outer.addLayout(row2)
        self._refresh(silent=True)

    def _refresh(self, *, silent: bool = False) -> None:
        self._block_test_buttons(True)
        try:
            conns = list_model_connections(self._config_root)
        except Exception as e:
            if not silent:
                QMessageBox.warning(self, "加载失败", str(e))
            return
        s = load_llm_settings(self._install_root)
        cur_default = s.default_model_connection_id
        self._default_combo.blockSignals(True)
        self._default_combo.clear()
        self._default_combo.addItem("（未指定：使用旧版 settings 中的密钥）", None)
        for c in conns:
            if not c.id:
                continue
            label = f"{c.name or c.id} ({c.id})"
            self._default_combo.addItem(label, c.id)
        idx = 0
        if cur_default:
            i = self._default_combo.findData(cur_default)
            if i >= 0:
                idx = i
        self._default_combo.setCurrentIndex(idx)
        self._default_combo.blockSignals(False)
        self._table.blockSignals(True)
        self._table.setRowCount(0)
        for ent in conns:
            if not ent.id:
                continue
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
            self._table.setItem(r, 1, QTableWidgetItem(ent.name or ent.id))
            self._table.setItem(r, 2, QTableWidgetItem(ent.model))
            url = ent.base_url or "（默认）"
            if len(url) > 48:
                url = url[:45] + "…"
            self._table.setItem(r, 3, QTableWidgetItem(url))
            st = self._status.get(ent.id, "未测试")
            self._table.setItem(r, 4, QTableWidgetItem(st))
            btn = QPushButton("测试", self)
            btn.clicked.connect(lambda *, eid=ent.id: self._run_tests([eid]))
            self._table.setCellWidget(r, 5, btn)
        self._table.blockSignals(False)
        self._block_test_buttons(False)

    def _block_test_buttons(self, block: bool) -> None:
        for i in range(self._table.rowCount()):
            w = self._table.cellWidget(i, 5)
            if w:
                w.setEnabled(not block)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() != 0:
            return
        cid = item.data(Qt.ItemDataRole.UserRole)
        if not cid:
            return
        try:
            conns = list_model_connections(self._config_root)
        except Exception:
            return
        ent = next((x for x in conns if x.id == cid), None)
        if ent is None:
            return
        enabled = item.checkState() == Qt.CheckState.Checked
        if ent.enabled == enabled:
            return
        try:
            save_model_connection_entry(
                ent.model_copy(update={"enabled": enabled}),
                config_root=self._config_root,
            )
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))
            self._refresh(silent=True)

    def _on_default_changed(self, _index: int) -> None:
        cid = self._default_combo.currentData()
        try:
            s = load_llm_settings(self._install_root)
            save_llm_settings(
                s.model_copy(update={"default_model_connection_id": cid}),
                self._install_root,
            )
        except Exception as e:
            QMessageBox.warning(self, "保存默认连接失败", str(e))

    def _selected_id(self) -> str | None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        r = rows[0].row()
        it = self._table.item(r, 0)
        if not it:
            return None
        return it.data(Qt.ItemDataRole.UserRole)

    def _on_new(self) -> None:
        dlg = ModelConnectionEditorDialog(install_root=self._install_root, parent=self)
        if dlg.exec():
            self._refresh(silent=True)

    def _on_edit(self) -> None:
        cid = self._selected_id()
        if not cid:
            QMessageBox.information(self, "编辑", "请先选中一行")
            return
        ent = load_model_connection(cid, config_root=self._config_root)
        if ent is None:
            QMessageBox.warning(self, "编辑", "找不到该连接配置")
            self._refresh(silent=True)
            return
        dlg = ModelConnectionEditorDialog(
            install_root=self._install_root, entry=ent, parent=self
        )
        if dlg.exec():
            self._refresh(silent=True)

    def _on_delete(self) -> None:
        cid = self._selected_id()
        if not cid:
            QMessageBox.information(self, "删除", "请先选中一行")
            return
        if QMessageBox.question(self, "删除", f"删除连接 {cid}？") != QMessageBox.StandardButton.Yes:
            return
        try:
            delete_model_connection_entry(cid, config_root=self._config_root)
            s = load_llm_settings(self._install_root)
            if s.default_model_connection_id == cid:
                save_llm_settings(
                    s.model_copy(update={"default_model_connection_id": None}),
                    self._install_root,
                )
        except Exception as e:
            QMessageBox.warning(self, "删除失败", str(e))
            return
        self._status.pop(cid, None)
        self._refresh(silent=True)

    def _on_test_selected(self) -> None:
        cid = self._selected_id()
        if not cid:
            QMessageBox.information(self, "测试", "请先选中一行")
            return
        self._run_tests([cid])

    def _on_test_all(self) -> None:
        try:
            conns = list_model_connections(self._config_root)
        except Exception as e:
            QMessageBox.warning(self, "加载失败", str(e))
            return
        ids = [c.id for c in conns if c.id]
        self._run_tests(ids)

    def _run_tests(self, ids: list[str]) -> None:
        if self._test_thread and self._test_thread.isRunning():
            return
        try:
            conns = {c.id: c for c in list_model_connections(self._config_root)}
        except Exception as e:
            QMessageBox.warning(self, "加载失败", str(e))
            return
        items = [(i, conns[i]) for i in ids if i in conns]
        if not items:
            return
        for cid, _ in items:
            self._status[cid] = "测试中…"
        self._update_status_cells()
        self._block_test_buttons(True)
        self._test_thread = _ConnectionTestThread(items, parent=self)
        self._test_thread.result.connect(self._on_test_result)
        self._test_thread.finished.connect(self._on_test_finished)
        self._test_thread.start()

    def _update_status_cells(self) -> None:
        for r in range(self._table.rowCount()):
            it0 = self._table.item(r, 0)
            if not it0:
                continue
            cid = it0.data(Qt.ItemDataRole.UserRole)
            if not cid:
                continue
            st = self._status.get(cid, "未测试")
            self._table.blockSignals(True)
            self._table.setItem(r, 4, QTableWidgetItem(st))
            self._table.blockSignals(False)

    def _on_test_result(self, cid: str, ok: bool, msg: str) -> None:
        self._status[cid] = "成功" if ok else f"失败: {msg}"
        self._update_status_cells()

    def _on_test_finished(self) -> None:
        self._block_test_buttons(False)
