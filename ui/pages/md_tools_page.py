# ui
import re
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor, QDesktopServices, QFont, QTextCursor, QTextFormat
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget
)

from core.text_cache import TextCache
from ui.md_tools_worker import MdToolsWorker

RENDER_LIMIT = 1500
PREVIEW_LIMIT = 200000
PREFIX_LEN = 12


class MdToolsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.files: list[Path] = []
        self._keys: set[str] = set()
        self._cache = TextCache()
        self._worker: MdToolsWorker | None = None
        self._op = ""
        self._payload = None
        self._extract_text = ""
        self._merge_text = ""
        self._current_file: str | None = None
        self._action_btns: list[QPushButton] = []
        self._setup_ui()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 24, 32, 24)
        lay.setSpacing(10)
        title = QLabel("ИНСТРУМЕНТЫ MARKDOWN")
        title.setObjectName("section_title")
        lay.addWidget(title)
        sep = QFrame()
        sep.setObjectName("separator")
        lay.addWidget(sep)

        file_row = QHBoxLayout()
        btn_files = QPushButton("Добавить файлы")
        btn_files.setObjectName("add_btn")
        btn_files.clicked.connect(self._add_files)
        file_row.addWidget(btn_files)
        btn_folder = QPushButton("Добавить папку")
        btn_folder.setObjectName("add_btn")
        btn_folder.clicked.connect(self._add_folder)
        file_row.addWidget(btn_folder)
        btn_clear = QPushButton("Очистить")
        btn_clear.setObjectName("danger_btn")
        btn_clear.clicked.connect(self._clear_files)
        file_row.addWidget(btn_clear)
        file_row.addStretch()
        self.files_lbl = QLabel("Файлов: 0")
        self.files_lbl.setObjectName("muted_label")
        file_row.addWidget(self.files_lbl)
        lay.addLayout(file_row)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_search_tab(), "🔎 Поиск")
        self.tabs.addTab(self._build_stats_tab(), "📊 Статистика")
        self.tabs.addTab(self._build_extract_tab(), "📤 Извлечение")
        self.tabs.addTab(self._build_merge_tab(), "🔗 Объединение")
        lay.addWidget(self.tabs, 1)

        self.progress = QProgressBar()
        self.progress.hide()
        lay.addWidget(self.progress)

        bottom = QHBoxLayout()
        self.status = QLabel("Готово к работе")
        self.status.setObjectName("muted_label")
        bottom.addWidget(self.status)
        bottom.addStretch()
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.setObjectName("add_btn")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel)
        bottom.addWidget(self.btn_cancel)
        lay.addLayout(bottom)

    def _build_search_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.setSpacing(8)
        row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Введите текст или регулярное выражение...")
        self.search_edit.returnPressed.connect(self._do_search)
        row.addWidget(self.search_edit)
        self.regex_cb = QCheckBox("Regex")
        row.addWidget(self.regex_cb)
        self.case_cb = QCheckBox("Учитывать регистр")
        row.addWidget(self.case_cb)
        btn = QPushButton("Найти")
        btn.setObjectName("connect_btn")
        btn.clicked.connect(self._do_search)
        self._action_btns.append(btn)
        row.addWidget(btn)
        lay.addLayout(row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(6)
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["Файл / Совпадение", "Строка"])
        self.results_tree.setColumnWidth(0, 420)
        self.results_tree.itemClicked.connect(self._on_result_clicked)
        ll.addWidget(self.results_tree, 1)
        info_row = QHBoxLayout()
        self.search_info = QLabel("")
        self.search_info.setObjectName("muted_label")
        info_row.addWidget(self.search_info)
        info_row.addStretch()
        self.btn_export_hits = QPushButton("Выгрузить все совпадения")
        self.btn_export_hits.setObjectName("add_btn")
        self.btn_export_hits.setEnabled(False)
        self.btn_export_hits.clicked.connect(self._export_hits)
        info_row.addWidget(self.btn_export_hits)
        ll.addLayout(info_row)
        splitter.addWidget(left)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(6)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Здесь появится контекст выбранного совпадения...")
        f = QFont("Consolas", 10)
        f.setStyleHint(QFont.StyleHint.Monospace)
        self.preview.setFont(f)
        rl.addWidget(self.preview, 1)
        btn_open = QPushButton("Открыть файл в редакторе")
        btn_open.setObjectName("add_btn")
        btn_open.clicked.connect(self._open_current_file)
        rl.addWidget(btn_open)
        splitter.addWidget(right)
        splitter.setSizes([520, 380])
        lay.addWidget(splitter, 1)
        return w

    def _build_stats_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.setSpacing(8)
        row = QHBoxLayout()
        btn = QPushButton("Рассчитать статистику")
        btn.setObjectName("connect_btn")
        btn.clicked.connect(self._do_stats)
        self._action_btns.append(btn)
        row.addWidget(btn)
        row.addStretch()
        lay.addLayout(row)
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(8)
        self.stats_table.setHorizontalHeaderLabels([
            "Файл", "Строк", "Слов", "Символов", "Код-блоков", "Заголовков", "Ссылок", "Изображений"
        ])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self.stats_table, 1)
        self.stats_summary = QLabel("")
        self.stats_summary.setObjectName("muted_label")
        self.stats_summary.setWordWrap(True)
        lay.addWidget(self.stats_summary)
        return w

    def _build_extract_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.setSpacing(8)
        info = QLabel("Извлечение элементов из всех загруженных MD-файлов. Содержимое code-блоков не участвует в подсчёте заголовков и ссылок.")
        info.setObjectName("muted_label")
        info.setWordWrap(True)
        lay.addWidget(info)
        row = QHBoxLayout()
        self.extract_combo = QComboBox()
        self.extract_combo.addItem("Кодовые блоки", "code")
        self.extract_combo.addItem("Заголовки", "headings")
        self.extract_combo.addItem("Ссылки", "links")
        self.extract_combo.addItem("Изображения", "images")
        row.addWidget(self.extract_combo)
        btn = QPushButton("Извлечь")
        btn.setObjectName("connect_btn")
        btn.clicked.connect(self._do_extract)
        self._action_btns.append(btn)
        row.addWidget(btn)
        self.btn_save_extract = QPushButton("Сохранить")
        self.btn_save_extract.setObjectName("add_btn")
        self.btn_save_extract.setEnabled(False)
        self.btn_save_extract.clicked.connect(lambda: self._save_result(self._extract_text, "extracted.md"))
        row.addWidget(self.btn_save_extract)
        self.extract_info = QLabel("")
        self.extract_info.setObjectName("muted_label")
        row.addWidget(self.extract_info)
        row.addStretch()
        lay.addLayout(row)
        self.extract_preview = QPlainTextEdit()
        self.extract_preview.setReadOnly(True)
        self.extract_preview.setPlaceholderText("Предпросмотр результатов...")
        lay.addWidget(self.extract_preview, 1)
        return w

    def _build_merge_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.setSpacing(8)
        info = QLabel("Объединение всех загруженных MD-файлов в один с указанием источника каждого блока.")
        info.setObjectName("muted_label")
        info.setWordWrap(True)
        lay.addWidget(info)
        row = QHBoxLayout()
        self.merge_sep_cb = QCheckBox("Добавлять разделители и заголовки файлов")
        self.merge_sep_cb.setChecked(True)
        row.addWidget(self.merge_sep_cb)
        btn = QPushButton("Объединить")
        btn.setObjectName("connect_btn")
        btn.clicked.connect(self._do_merge)
        self._action_btns.append(btn)
        row.addWidget(btn)
        self.btn_save_merge = QPushButton("Сохранить")
        self.btn_save_merge.setObjectName("add_btn")
        self.btn_save_merge.setEnabled(False)
        self.btn_save_merge.clicked.connect(lambda: self._save_result(self._merge_text, "merged.md"))
        row.addWidget(self.btn_save_merge)
        self.merge_info = QLabel("")
        self.merge_info.setObjectName("muted_label")
        row.addWidget(self.merge_info)
        row.addStretch()
        lay.addLayout(row)
        self.merge_preview = QPlainTextEdit()
        self.merge_preview.setReadOnly(True)
        self.merge_preview.setPlaceholderText("Предпросмотр объединённого файла...")
        lay.addWidget(self.merge_preview, 1)
        return w

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Выберите MD-файлы", "",
            "Markdown Files (*.md *.markdown);;All Files (*)"
        )
        if paths:
            self._register_files([Path(p) for p in paths])

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Папка с MD-файлами")
        if not folder:
            return
        found = []
        for ext in ("*.md", "*.markdown"):
            found.extend(Path(folder).rglob(ext))
        if found:
            self._register_files(found)
        else:
            QMessageBox.information(self, "Информация", "В папке не найдено MD-файлов")

    def _register_files(self, new_files: list[Path]):
        added = 0
        for f in new_files:
            key = str(f)
            if key in self._keys or not f.is_file():
                continue
            self.files.append(f)
            self._keys.add(key)
            added += 1
        self.files_lbl.setText(f"Файлов: {len(self.files)}" + (f" (+{added})" if added else ""))

    def _clear_files(self):
        self.files.clear()
        self._keys.clear()
        self._cache.clear()
        self._payload = None
        self._extract_text = ""
        self._merge_text = ""
        self._current_file = None
        self.results_tree.clear()
        self.preview.clear()
        self.search_info.setText("")
        self.stats_table.setRowCount(0)
        self.stats_summary.setText("")
        self.extract_preview.clear()
        self.merge_preview.clear()
        self.extract_info.setText("")
        self.merge_info.setText("")
        self.btn_export_hits.setEnabled(False)
        self.btn_save_extract.setEnabled(False)
        self.btn_save_merge.setEnabled(False)
        self.files_lbl.setText("Файлов: 0")

    def _run(self, op: str, params: dict):
        if self._worker and self._worker.isRunning():
            self.status.setText("⚠️ Операция уже выполняется")
            return
        if not self.files:
            QMessageBox.information(self, "Информация", "Сначала добавьте MD-файлы")
            return
        self._op = op
        self.progress.show()
        self.progress.setValue(0)
        self.btn_cancel.setEnabled(True)
        for b in self._action_btns:
            b.setEnabled(False)
        self.status.setText("Обработка...")
        self._worker = MdToolsWorker(op, [str(f) for f in self.files], params)
        self._worker.progress.connect(self._on_progress)
        self._worker.done.connect(self._on_done)
        self._worker.start()

    def _on_progress(self, value: int, name: str):
        self.progress.setValue(value)
        self.status.setText(f"Обработка: {name}")

    def _cancel(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self.status.setText("Отмена...")

    def _on_done(self, ok: bool, msg: str, payload):
        self.progress.hide()
        self.btn_cancel.setEnabled(False)
        for b in self._action_btns:
            b.setEnabled(True)
        if not ok:
            prefix = "⚠️ " if msg == "Отменено" else "❌ "
            self.status.setText(prefix + msg)
            return
        if self._op == "search":
            self._render_search(payload)
        elif self._op == "stats":
            self._render_stats(payload)
        elif self._op == "extract":
            self._extract_text = payload["text"]
            self._fill_preview(self.extract_preview, self._extract_text)
            self.extract_info.setText(f"Элементов: {payload['count']}")
            self.btn_save_extract.setEnabled(bool(self._extract_text.strip()))
            self.status.setText(f"✅ Извлечено {payload['count']}")
        elif self._op == "merge":
            self._merge_text = payload["text"]
            self._fill_preview(self.merge_preview, self._merge_text)
            self.merge_info.setText(f"Символов: {len(self._merge_text)}")
            self.btn_save_merge.setEnabled(bool(self._merge_text.strip()))
            self.status.setText("✅ Объединено")

    def _fill_preview(self, widget: QPlainTextEdit, text: str):
        if len(text) > PREVIEW_LIMIT:
            widget.setPlainText(text[:PREVIEW_LIMIT] + "\n\n… предпросмотр обрезан, файл сохранится целиком")
        else:
            widget.setPlainText(text)

    def _do_search(self):
        pattern = self.search_edit.text()
        if not pattern:
            return
        flags = 0 if self.case_cb.isChecked() else re.IGNORECASE
        if self.regex_cb.isChecked():
            try:
                re.compile(pattern, flags)
            except re.error as err:
                QMessageBox.warning(self, "Ошибка regex", str(err))
                return
        self.preview.clear()
        self._current_file = None
        self._run("search", {
            "pattern": pattern,
            "regex": self.regex_cb.isChecked(),
            "case": self.case_cb.isChecked()
        })

    def _render_search(self, payload):
        self._payload = payload
        self.results_tree.setUpdatesEnabled(False)
        self.results_tree.clear()
        shown = 0
        for fh in payload["files"]:
            path = Path(fh.path)
            top = QTreeWidgetItem([f"{path.name}  ({len(fh.hits)})", str(path.parent)])
            top.setData(0, Qt.ItemDataRole.UserRole, None)
            self.results_tree.addTopLevelItem(top)
            for hit in fh.hits:
                if shown >= RENDER_LIMIT:
                    break
                child = QTreeWidgetItem([hit.snippet, str(hit.line + 1)])
                child.setData(0, Qt.ItemDataRole.UserRole, {
                    "file": fh.path,
                    "line": hit.line,
                    "match_start": hit.start,
                    "match_end": hit.end
                })
                top.addChild(child)
                shown += 1
            top.setExpanded(shown < RENDER_LIMIT)
        self.results_tree.setUpdatesEnabled(True)
        total = payload["total"]
        note = " (достигнут лимит сбора)" if payload["truncated"] else ""
        self.results_tree.setHeaderLabels([f"Найдено: {total}{note}", "Строка"])
        self.search_info.setText(f"Показано {shown} из {total}")
        self.btn_export_hits.setEnabled(total > 0)
        self.status.setText(f"✅ Найдено {total} в {len(payload['files'])} файлах")

    def _export_hits(self):
        if not self._payload:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить совпадения", "matches.txt", "Text Files (*.txt)")
        if not path:
            return
        lines = []
        for fh in self._payload["files"]:
            lines.append(fh.path)
            for hit in fh.hits:
                lines.append(f"  {hit.line + 1}: {hit.snippet}")
            lines.append("")
        Path(path).write_text("\n".join(lines), encoding="utf-8")
        self.status.setText("✅ Совпадения сохранены")

    def _on_result_clicked(self, item: QTreeWidgetItem, _col: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        self._current_file = data["file"]
        self._show_context(data["file"], data["line"], data["match_start"], data["match_end"])

    def _show_context(self, file_path: str, line_no: int, m_start: int, m_end: int):
        try:
            text = self._cache.get(file_path)
        except Exception as err:
            self.preview.setPlainText(f"Ошибка чтения: {err}")
            return
        lines = text.splitlines()
        start = max(0, line_no - 3)
        end = min(len(lines), line_no + 4)
        out = []
        for i in range(start, end):
            prefix = ">>> " if i == line_no else "    "
            out.append(f"{prefix}{i + 1:5d} | {lines[i]}")
        self.preview.setPlainText("\n".join(out))
        base = self.preview.textCursor()
        base.movePosition(QTextCursor.MoveOperation.Start)
        base.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, line_no - start)
        self.preview.setTextCursor(base)
        self.preview.centerCursor()
        mark = QTextCursor(base)
        mark.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, PREFIX_LEN + m_start)
        mark.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, max(m_end - m_start, 1))
        sel = QPlainTextEdit.ExtraSelection()
        sel.cursor = mark
        sel.format.setBackground(QColor(255, 158, 67, 90))
        sel.format.setProperty(QTextFormat.Property.FullWidthSelection, False)
        self.preview.setExtraSelections([sel])

    def _open_current_file(self):
        if self._current_file:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._current_file))

    def _do_stats(self):
        self._run("stats", {})

    def _render_stats(self, rows):
        keys = ("lines", "words", "chars", "code", "headings", "links", "images")
        totals = dict.fromkeys(keys, 0)
        self.stats_table.setUpdatesEnabled(False)
        self.stats_table.setRowCount(0)
        for st in rows:
            r = self.stats_table.rowCount()
            self.stats_table.insertRow(r)
            values = [Path(st.path).name, st.lines, st.words, st.chars, st.code, st.headings, st.links, st.images]
            for col, val in enumerate(values):
                self.stats_table.setItem(r, col, QTableWidgetItem(str(val)))
            for k in keys:
                totals[k] += getattr(st, k)
        self.stats_table.setUpdatesEnabled(True)
        self.stats_summary.setText(
            f"ИТОГО: строк {totals['lines']}, слов {totals['words']}, символов {totals['chars']}, "
            f"код-блоков {totals['code']}, заголовков {totals['headings']}, "
            f"ссылок {totals['links']}, изображений {totals['images']}"
        )
        self.status.setText(f"✅ Посчитано файлов: {len(rows)}")

    def _do_extract(self):
        self._run("extract", {"kind": self.extract_combo.currentData()})

    def _do_merge(self):
        self._run("merge", {"sep": self.merge_sep_cb.isChecked()})

    def _save_result(self, text: str, default_name: str):
        if not text.strip():
            return
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить результат", default_name, "Markdown Files (*.md)")
        if not path:
            return
        Path(path).write_text(text, encoding="utf-8")
        self.status.setText("✅ Сохранено")

    def shutdown(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(3000)