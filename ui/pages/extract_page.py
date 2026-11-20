# ui
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QTreeWidgetItemIterator,
    QVBoxLayout,
    QWidget
)

from core.request import ExtractRequest
from core.selector import FileSelector
from ui.scan_worker import ScanWorker


def _fmt_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / 1024 / 1024:.1f} MB"


class DropLabel(QLabel):
    file_dropped = pyqtSignal(str)
    invalid_dropped = pyqtSignal(str)

    def __init__(self):
        super().__init__("📦 Перетащите .zip архив сюда или нажмите «Выбрать архив»")
        self.setObjectName("drop_zone")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAcceptDrops(True)
        self.setProperty("drop", False)
        self.setWordWrap(True)

    def _set_drop(self, value: bool):
        self.setProperty("drop", value)
        self.style().unpolish(self)
        self.style().polish(self)

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            self._set_drop(True)
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragLeaveEvent(self, e):
        self._set_drop(False)

    def dropEvent(self, e: QDropEvent):
        self._set_drop(False)
        urls = e.mimeData().urls()
        if not urls:
            e.ignore()
            return
        for url in urls:
            path = url.toLocalFile()
            if path.lower().endswith(".zip") and Path(path).is_file():
                e.acceptProposedAction()
                self.file_dropped.emit(path)
                return
        e.ignore()
        self.invalid_dropped.emit("⚠️ Требуется .zip архив")


class ExtractPage(QWidget):
    extract_requested = pyqtSignal(object)
    open_dir_requested = pyqtSignal()
    open_file_requested = pyqtSignal(str)
    cancel_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.zip_path = None
        self.output_path = None
        self.entries: list[tuple[str, int]] = []
        self._folders: set[str] = set()
        self._files: set[str] = set()
        self._scan: ScanWorker | None = None
        self._scanning = False
        self._working = False
        self._setup_ui()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 20, 28, 20)
        lay.setSpacing(8)
        lay.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)

        title = QLabel("ЭКСТРАКЦИЯ АРХИВА")
        title.setObjectName("section_title")
        lay.addWidget(title)
        sep = QFrame()
        sep.setObjectName("separator")
        lay.addWidget(sep)

        self.drop_lbl = DropLabel()
        self.drop_lbl.setFixedHeight(84)
        self.drop_lbl.file_dropped.connect(self.set_zip)
        self.drop_lbl.invalid_dropped.connect(self._set_status)
        lay.addWidget(self.drop_lbl)

        controls = QHBoxLayout()
        self.btn_browse = QPushButton("Выбрать архив")
        self.btn_browse.setObjectName("add_btn")
        self.btn_browse.clicked.connect(self._browse_zip)
        controls.addWidget(self.btn_browse)

        preset_lbl = QLabel("Конфигурация:")
        preset_lbl.setObjectName("muted_label")
        controls.addWidget(preset_lbl)
        self.preset_cb = QComboBox()
        self.preset_cb.currentIndexChanged.connect(self._refresh_actions)
        controls.addWidget(self.preset_cb)

        fmt_lbl = QLabel("Формат:")
        fmt_lbl.setObjectName("muted_label")
        controls.addWidget(fmt_lbl)
        self.format_cb = QComboBox()
        self.format_cb.addItem("MD", "md")
        self.format_cb.addItem("TXT", "txt")
        self.format_cb.currentIndexChanged.connect(self._on_format_changed)
        controls.addWidget(self.format_cb)
        controls.addStretch()
        lay.addLayout(controls)

        mode_row = QHBoxLayout()
        mode_lbl = QLabel("Выборка:")
        mode_lbl.setObjectName("muted_label")
        mode_row.addWidget(mode_lbl)
        self.mode_cb = QComboBox()
        self.mode_cb.addItem("Весь архив", "all")
        self.mode_cb.addItem("Папка", "folder")
        self.mode_cb.addItem("Файлы", "file")
        self.mode_cb.addItem("По содержимому", "content")
        self.mode_cb.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self.mode_cb)
        self.scan_info = QLabel("")
        self.scan_info.setObjectName("muted_label")
        mode_row.addWidget(self.scan_info)
        mode_row.addStretch()
        lay.addLayout(mode_row)

        self.mode_stack = QStackedWidget()
        self.mode_stack.addWidget(self._build_all_page())
        self.mode_stack.addWidget(self._build_folder_page())
        self.mode_stack.addWidget(self._build_file_page())
        self.mode_stack.addWidget(self._build_content_page())
        self.mode_stack.setMinimumHeight(120)
        lay.addWidget(self.mode_stack, 1)

        actions = QHBoxLayout()
        self.btn_extract = QPushButton("Извлечь в MD")
        self.btn_extract.setObjectName("connect_btn")
        self.btn_extract.setEnabled(False)
        self.btn_extract.clicked.connect(self._on_extract_click)
        actions.addWidget(self.btn_extract)

        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.setObjectName("add_btn")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._on_cancel)
        actions.addWidget(self.btn_cancel)
        actions.addStretch()

        self.btn_open_file = QPushButton("Открыть файл")
        self.btn_open_file.setObjectName("add_btn")
        self.btn_open_file.setEnabled(False)
        self.btn_open_file.clicked.connect(self._open_file)
        actions.addWidget(self.btn_open_file)

        self.btn_open_dir = QPushButton("Открыть папку")
        self.btn_open_dir.setObjectName("add_btn")
        self.btn_open_dir.clicked.connect(lambda: self.open_dir_requested.emit())
        actions.addWidget(self.btn_open_dir)
        lay.addLayout(actions)

        self.progress = QProgressBar()
        self.progress.hide()
        lay.addWidget(self.progress)
        self.current_file = QLabel("")
        self.current_file.setObjectName("muted_label")
        lay.addWidget(self.current_file)

        status_row = QHBoxLayout()
        self.status = QLabel("Готово к работе")
        self.status.setObjectName("section_title")
        status_row.addWidget(self.status)
        status_row.addStretch()
        lay.addLayout(status_row)

        hint = QLabel("MD — для чтения глазами, TXT — экономный дамп для ИИ. Полный список файлов архива попадает в дамп всегда.")
        hint.setObjectName("muted_label")
        hint.setWordWrap(True)
        lay.addWidget(hint)

    def _build_all_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel("Будут включены все текстовые файлы архива, кроме исключённых в настройках.")
        lbl.setObjectName("muted_label")
        lbl.setWordWrap(True)
        lay.addWidget(lbl)
        lay.addStretch()
        return w

    def _build_folder_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabels(["Папка", "Файлов"])
        self.folder_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.folder_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.folder_tree.setMinimumHeight(0)
        self.folder_tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        self.folder_tree.itemChanged.connect(self._on_folder_changed)
        lay.addWidget(self.folder_tree, 1)
        row = QHBoxLayout()
        btn = QPushButton("Снять все")
        btn.setObjectName("add_btn")
        btn.clicked.connect(self._clear_folders)
        row.addWidget(btn)
        self.folder_count = QLabel("Выбрано: 0")
        self.folder_count.setObjectName("muted_label")
        row.addWidget(self.folder_count)
        row.addStretch()
        lay.addLayout(row)
        return w

    def _build_file_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        self.file_filter = QLineEdit()
        self.file_filter.setPlaceholderText("Фильтр по имени файла (только для навигации)...")
        self.file_filter.textChanged.connect(self._apply_file_filter)
        lay.addWidget(self.file_filter)
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(0)
        self.file_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        self.file_list.itemChanged.connect(self._on_file_changed)
        lay.addWidget(self.file_list, 1)
        row = QHBoxLayout()
        btn_all = QPushButton("Выбрать видимые")
        btn_all.setObjectName("add_btn")
        btn_all.clicked.connect(self._select_visible)
        row.addWidget(btn_all)
        btn_none = QPushButton("Снять все")
        btn_none.setObjectName("add_btn")
        btn_none.clicked.connect(self._clear_files)
        row.addWidget(btn_none)
        self.file_count = QLabel("Выбрано: 0")
        self.file_count.setObjectName("muted_label")
        row.addWidget(self.file_count)
        row.addStretch()
        lay.addLayout(row)
        return w

    def _build_content_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        self.query_edit = QLineEdit()
        self.query_edit.setPlaceholderText("Текст или regex для поиска внутри файлов...")
        lay.addWidget(self.query_edit)
        row = QHBoxLayout()
        self.regex_cb = QCheckBox("Regex")
        row.addWidget(self.regex_cb)
        self.case_cb = QCheckBox("Учитывать регистр")
        row.addWidget(self.case_cb)
        row.addStretch()
        lay.addLayout(row)
        lbl = QLabel("Поиск только по содержимому текстовых файлов. Файлы сверх лимита размера и бинарные не участвуют.")
        lbl.setObjectName("muted_label")
        lbl.setWordWrap(True)
        lay.addWidget(lbl)
        lay.addStretch()
        return w

    def _set_status(self, text: str):
        self.status.setText(text)

    def _on_mode_changed(self):
        self.mode_stack.setCurrentIndex(max(self.mode_cb.currentIndex(), 0))

    def _on_format_changed(self):
        self.btn_extract.setText("Извлечь в TXT" if self.format_cb.currentData() == "txt" else "Извлечь в MD")

    def set_zip(self, path: str):
        self._stop_scan()
        self.zip_path = path
        self.output_path = None
        self.entries = []
        self._folders.clear()
        self._files.clear()
        self.folder_tree.blockSignals(True)
        self.folder_tree.clear()
        self.folder_tree.blockSignals(False)
        self.file_list.blockSignals(True)
        self.file_list.clear()
        self.file_list.blockSignals(False)
        self.file_filter.clear()
        self.folder_count.setText("Выбрано: 0")
        self.file_count.setText("Выбрано: 0")
        self.btn_open_file.setEnabled(False)
        self.drop_lbl.setText(f"📦 Выбран: {Path(path).name}")
        self._start_scan()

    def _start_scan(self):
        self._scanning = True
        self.scan_info.setText("Сканирование...")
        self.progress.show()
        self.progress.setValue(0)
        self.btn_cancel.setEnabled(True)
        self.btn_browse.setEnabled(False)
        self.status.setText("Сканирование архива...")
        self._refresh_actions()
        self._scan = ScanWorker(self.zip_path)
        self._scan.progress.connect(self.set_progress)
        self._scan.finished.connect(self._on_scan_done)
        self._scan.start()

    def _stop_scan(self):
        if self._scan and self._scan.isRunning():
            self._scan.cancel()
            self._scan.wait(3000)
        self._scanning = False

    def _on_scan_done(self, ok: bool, msg: str, entries):
        self._scanning = False
        self.progress.hide()
        self.current_file.setText("")
        self.btn_browse.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        if not ok:
            self.entries = []
            self.scan_info.setText("")
            prefix = "⚠️ " if msg == "Отменено" else "❌ "
            self.status.setText(prefix + msg)
            self._refresh_actions()
            return
        self.entries = entries
        self._build_folder_tree([p for p, _ in entries])
        self._fill_file_list(entries)
        self.scan_info.setText(f"Файлов в архиве: {len(entries)}")
        self.status.setText("Готово к извлечению" if entries else "⚠️ Архив пуст")
        self._refresh_actions()

    def _build_folder_tree(self, paths: list[str]):
        counts: dict[str, int] = {}
        for p in paths:
            acc = ""
            for part in p.split("/")[:-1]:
                acc = f"{acc}/{part}" if acc else part
                counts[acc] = counts.get(acc, 0) + 1
        self.folder_tree.blockSignals(True)
        self.folder_tree.clear()
        root = self.folder_tree.invisibleRootItem()
        nodes: dict[str, QTreeWidgetItem] = {}
        for d in sorted(counts):
            parent_path = d.rsplit("/", 1)[0] if "/" in d else ""
            parent = nodes.get(parent_path, root)
            item = QTreeWidgetItem([d.rsplit("/", 1)[-1], str(counts[d])])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(0, Qt.CheckState.Unchecked)
            item.setData(0, Qt.ItemDataRole.UserRole, d)
            parent.addChild(item)
            nodes[d] = item
        self.folder_tree.blockSignals(False)

    def _fill_file_list(self, entries: list[tuple[str, int]]):
        self.file_list.blockSignals(True)
        self.file_list.clear()
        for path, size in entries:
            item = QListWidgetItem(f"{path}  ({_fmt_size(size)})")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.file_list.addItem(item)
        self.file_list.blockSignals(False)

    def _on_folder_changed(self, item: QTreeWidgetItem, col: int):
        if col != 0:
            return
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if item.checkState(0) == Qt.CheckState.Checked:
            self._folders.add(path)
        else:
            self._folders.discard(path)
        self.folder_count.setText(f"Выбрано: {len(self._folders)}")

    def _on_file_changed(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if item.checkState() == Qt.CheckState.Checked:
            self._files.add(path)
        else:
            self._files.discard(path)
        self.file_count.setText(f"Выбрано: {len(self._files)}")

    def _apply_file_filter(self, text: str):
        needle = text.strip().lower()
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            path = item.data(Qt.ItemDataRole.UserRole)
            item.setHidden(bool(needle) and needle not in path.lower())

    def _select_visible(self):
        self.file_list.blockSignals(True)
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.CheckState.Checked)
                self._files.add(item.data(Qt.ItemDataRole.UserRole))
        self.file_list.blockSignals(False)
        self.file_count.setText(f"Выбрано: {len(self._files)}")

    def _clear_files(self):
        self.file_list.blockSignals(True)
        for i in range(self.file_list.count()):
            self.file_list.item(i).setCheckState(Qt.CheckState.Unchecked)
        self.file_list.blockSignals(False)
        self._files.clear()
        self.file_count.setText("Выбрано: 0")

    def _clear_folders(self):
        self.folder_tree.blockSignals(True)
        it = QTreeWidgetItemIterator(self.folder_tree)
        while it.value():
            it.value().setCheckState(0, Qt.CheckState.Unchecked)
            it += 1
        self.folder_tree.blockSignals(False)
        self._folders.clear()
        self.folder_count.setText("Выбрано: 0")

    def update_presets(self, presets: dict):
        current = self.preset_cb.currentText()
        self.preset_cb.blockSignals(True)
        self.preset_cb.clear()
        for name in sorted(presets.keys()):
            self.preset_cb.addItem(name)
        if current in presets:
            self.preset_cb.setCurrentText(current)
        elif self.preset_cb.count():
            self.preset_cb.setCurrentIndex(0)
        self.preset_cb.blockSignals(False)
        self._refresh_actions()

    def _refresh_actions(self):
        ready = (
            bool(self.zip_path)
            and bool(self.entries)
            and bool(self.preset_cb.currentText())
            and not self._scanning
            and not self._working
        )
        self.btn_extract.setEnabled(ready)

    def set_working(self):
        self._working = True
        self.btn_cancel.setEnabled(True)
        self.btn_browse.setEnabled(False)
        self.preset_cb.setEnabled(False)
        self.format_cb.setEnabled(False)
        self.mode_cb.setEnabled(False)
        self.mode_stack.setEnabled(False)
        self.btn_open_file.setEnabled(False)
        self.btn_open_dir.setEnabled(False)
        self.progress.show()
        self.progress.setValue(0)
        self.current_file.setText("")
        self.status.setText("Обработка...")
        self._refresh_actions()

    def set_progress(self, value: int, filename: str):
        self.progress.setValue(value)
        if len(filename) > 90:
            filename = "…" + filename[-90:]
        self.current_file.setText(filename)

    def set_done(self, ok: bool, message: str, output_path: str | None = None):
        self._working = False
        self.btn_cancel.setEnabled(False)
        self.btn_browse.setEnabled(True)
        self.preset_cb.setEnabled(True)
        self.format_cb.setEnabled(True)
        self.mode_cb.setEnabled(True)
        self.mode_stack.setEnabled(True)
        self.btn_open_dir.setEnabled(True)
        self.progress.hide()
        self.current_file.setText("")
        if ok:
            self.output_path = output_path
            self.status.setText("✅ Успешно")
            self.btn_open_file.setEnabled(bool(output_path))
        else:
            self.output_path = None
            prefix = "⚠️ " if message == "Отменено" else "❌ "
            self.status.setText(prefix + message)
            self.btn_open_file.setEnabled(False)
        self._refresh_actions()

    def _browse_zip(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите ZIP", "", "ZIP Files (*.zip)")
        if path:
            self.set_zip(path)

    def _open_file(self):
        if self.output_path:
            self.open_file_requested.emit(self.output_path)

    def _on_cancel(self):
        if self._scanning and self._scan:
            self._scan.cancel()
            self.status.setText("Отмена сканирования...")
        else:
            self.cancel_requested.emit()

    def _on_extract_click(self):
        if not self.zip_path:
            return
        if not self.preset_cb.currentText():
            self.status.setText("⚠️ Нет активного пресета")
            return
        if self._scanning:
            self.status.setText("⚠️ Дождитесь сканирования архива")
            return
        mode = self.mode_cb.currentData()
        folders = sorted(self._folders)
        files = sorted(self._files)
        query = self.query_edit.text()
        if mode == "folder" and not folders:
            self.status.setText("⚠️ Отметьте хотя бы одну папку")
            return
        if mode == "file" and not files:
            self.status.setText("⚠️ Отметьте хотя бы один файл")
            return
        if mode == "content" and not query.strip():
            self.status.setText("⚠️ Введите поисковый запрос")
            return
        try:
            selector = FileSelector(
                mode=mode,
                folders=folders,
                files=files,
                query=query,
                is_regex=self.regex_cb.isChecked(),
                case_sensitive=self.case_cb.isChecked()
            )
        except ValueError as err:
            QMessageBox.warning(self, "Ошибка regex", str(err))
            return
        self.extract_requested.emit(
            ExtractRequest(self.zip_path, self.preset_cb.currentText(), self.format_cb.currentData(), selector)
        )

    def shutdown(self):
        self._stop_scan()