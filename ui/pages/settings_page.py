# Файл: ui/pages/settings_page.py
import json
from pathlib import Path

from PyQt6.QtCore import pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget
)
from dataclasses import replace
from core.config_manager import delete_preset, ensure_default, load_presets, save_preset
from core.models import AppSettings
from core.settings import save_settings


class SettingsPage(QWidget):
    settings_saved = pyqtSignal(object)
    presets_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.presets = {}
        self._base = AppSettings()
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 32, 32, 32)
        outer.setSpacing(14)

        title = QLabel("НАСТРОЙКИ")
        title.setObjectName("section_title")
        outer.addWidget(title)

        sep = QFrame()
        sep.setObjectName("separator")
        outer.addWidget(sep)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        container.setObjectName("settings_container")

        self.lay = QVBoxLayout(container)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(12)

        self._build_general()
        self._build_extraction()
        self._build_markdown()
        self._build_presets()

        self.lay.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

        bottom = QHBoxLayout()

        self.save_status = QLabel("")
        self.save_status.setObjectName("muted_label")
        bottom.addWidget(self.save_status)

        bottom.addStretch()

        self.btn_save = QPushButton("Сохранить настройки")
        self.btn_save.setObjectName("connect_btn")
        self.btn_save.clicked.connect(self._save_settings)
        bottom.addWidget(self.btn_save)

        outer.addLayout(bottom)

    def _card(self, title: str) -> QVBoxLayout:
        card = QFrame()
        card.setObjectName("card")

        lay = QVBoxLayout(card)
        lay.setSpacing(8)

        lbl = QLabel(title)
        lbl.setObjectName("card_title")
        lay.addWidget(lbl)

        self.lay.addWidget(card)
        return lay

    def _build_general(self):
        lay = self._card("ОСНОВНЫЕ")

        row = QHBoxLayout()
        lbl = QLabel("Выходная папка")
        lbl.setObjectName("muted_label")
        lbl.setFixedWidth(170)
        row.addWidget(lbl)

        self.out_dir_edit = QLineEdit()
        row.addWidget(self.out_dir_edit)

        btn_browse = QPushButton("Обзор")
        btn_browse.setObjectName("add_btn")
        btn_browse.clicked.connect(self._browse_output_dir)
        row.addWidget(btn_browse)

        btn_open = QPushButton("Открыть")
        btn_open.setObjectName("add_btn")
        btn_open.clicked.connect(self._open_output_dir)
        row.addWidget(btn_open)

        lay.addLayout(row)

        row2 = QHBoxLayout()
        lbl2 = QLabel("После извлечения")
        lbl2.setObjectName("muted_label")
        lbl2.setFixedWidth(170)
        row2.addWidget(lbl2)

        self.after_combo = QComboBox()
        self.after_combo.addItem("Открыть папку", "open_folder")
        self.after_combo.addItem("Открыть файл", "open_file")
        self.after_combo.addItem("Ничего не делать", "none")
        row2.addWidget(self.after_combo)

        lay.addLayout(row2)

        row3 = QHBoxLayout()
        lbl3 = QLabel("Тема")
        lbl3.setObjectName("muted_label")
        lbl3.setFixedWidth(170)
        row3.addWidget(lbl3)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Светлая", "light")
        self.theme_combo.addItem("Тёмная", "dark")
        row3.addWidget(self.theme_combo)

        lay.addLayout(row3)

    def _build_extraction(self):
        lay = self._card("ЭКСТРАКЦИЯ")

        row = QHBoxLayout()
        lbl = QLabel("Лимит размера файла")
        lbl.setObjectName("muted_label")
        lbl.setFixedWidth(170)
        row.addWidget(lbl)

        self.max_spin = QSpinBox()
        self.max_spin.setRange(0, 1048576)
        self.max_spin.setSuffix(" KB")
        self.max_spin.setSpecialValueText("Без лимита")
        row.addWidget(self.max_spin)

        lay.addLayout(row)

        row2 = QHBoxLayout()
        lbl2 = QLabel("Кодировка fallback")
        lbl2.setObjectName("muted_label")
        lbl2.setFixedWidth(170)
        row2.addWidget(lbl2)

        self.enc_combo = QComboBox()
        self.enc_combo.setEditable(True)
        self.enc_combo.addItems(["utf-8", "cp1251", "latin-1"])
        row2.addWidget(self.enc_combo)

        lay.addLayout(row2)

        row3 = QHBoxLayout()
        lbl3 = QLabel("Исключения")
        lbl3.setObjectName("muted_label")
        lbl3.setFixedWidth(170)
        row3.addWidget(lbl3)

        self.exclude_edit = QPlainTextEdit()
        self.exclude_edit.setPlaceholderText(".git\nnode_modules\n__pycache__\n*.pyc")
        self.exclude_edit.setFixedHeight(110)
        row3.addWidget(self.exclude_edit)

        lay.addLayout(row3)

    def _build_markdown(self):
        lay = self._card("ФОРМАТ MARKDOWN")

        self.stats_cb = QCheckBox("Добавлять статистику")
        self.code_map_cb = QCheckBox("Добавлять карту кода")
        self.binary_map_cb = QCheckBox("Добавлять карту бинарных/прочих файлов")
        self.content_cb = QCheckBox("Добавлять содержимое файлов")

        lay.addWidget(self.stats_cb)
        lay.addWidget(self.code_map_cb)
        lay.addWidget(self.binary_map_cb)
        lay.addWidget(self.content_cb)

    def _build_presets(self):
        lay = self._card("ПРЕСЕТЫ")

        row = QHBoxLayout()
        lbl = QLabel("Текущий пресет")
        lbl.setObjectName("muted_label")
        lbl.setFixedWidth(170)
        row.addWidget(lbl)

        self.preset_cb = QComboBox()
        row.addWidget(self.preset_cb)

        btn_new = QPushButton("Новый")
        btn_new.setObjectName("add_btn")
        btn_new.clicked.connect(self._new_preset)
        row.addWidget(btn_new)

        btn_dup = QPushButton("Дублировать")
        btn_dup.setObjectName("add_btn")
        btn_dup.clicked.connect(self._duplicate_preset)
        row.addWidget(btn_dup)

        btn_del = QPushButton("Удалить")
        btn_del.setObjectName("danger_btn")
        btn_del.clicked.connect(self._delete_preset)
        row.addWidget(btn_del)

        lay.addLayout(row)

        self.ext_edit = QPlainTextEdit()
        self.ext_edit.setPlaceholderText(".py .js .ts\nМожно писать через пробел, запятую или с новой строки")
        self.ext_edit.setFixedHeight(140)
        lay.addWidget(self.ext_edit)

        row2 = QHBoxLayout()

        btn_save_preset = QPushButton("Сохранить пресет")
        btn_save_preset.setObjectName("connect_btn")
        btn_save_preset.clicked.connect(self._save_preset)
        row2.addWidget(btn_save_preset)

        btn_import = QPushButton("Импорт")
        btn_import.setObjectName("add_btn")
        btn_import.clicked.connect(self._import_preset)
        row2.addWidget(btn_import)

        btn_export = QPushButton("Экспорт")
        btn_export.setObjectName("add_btn")
        btn_export.clicked.connect(self._export_preset)
        row2.addWidget(btn_export)

        row2.addStretch()
        lay.addLayout(row2)

        self.preset_cb.currentTextChanged.connect(self._load_preset_extensions)

    def load(self, settings: AppSettings, presets: dict):
        self._load_settings(settings)
        self._load_presets(presets)

    def _load_settings(self, settings: AppSettings):
        self._base = settings
        self.out_dir_edit.setText(settings.output_dir)
        self._set_combo_by_data(self.after_combo, settings.after_action)
        self._set_combo_by_data(self.theme_combo, settings.theme)
        self.max_spin.setValue(int(settings.max_file_kb))
        self.exclude_edit.setPlainText("\n".join(settings.exclude_patterns))

        index = self.enc_combo.findText(settings.fallback_encoding)
        if index >= 0:
            self.enc_combo.setCurrentIndex(index)
        else:
            self.enc_combo.setEditText(settings.fallback_encoding)

        self.stats_cb.setChecked(settings.include_stats)
        self.code_map_cb.setChecked(settings.include_code_map)
        self.binary_map_cb.setChecked(settings.include_binary_map)
        self.content_cb.setChecked(settings.include_content)

    def _load_presets(self, presets: dict):
        self.presets = presets
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
        self._load_preset_extensions()

    def _load_preset_extensions(self):
        name = self.preset_cb.currentText()
        self.ext_edit.setPlainText("\n".join(self.presets.get(name, [])))

    def _parse_extensions(self) -> list[str]:
        text = self.ext_edit.toPlainText().replace(",", " ")
        items = []

        for token in text.split():
            token = token.strip().lower()

            if not token:
                continue

            if not token.startswith("."):
                token = f".{token}"

            if token not in items:
                items.append(token)

        return items

    def _collect_settings(self) -> AppSettings:
        defaults = AppSettings()

        output_dir = self.out_dir_edit.text().strip() or defaults.output_dir
        excludes = [line.strip() for line in self.exclude_edit.toPlainText().splitlines() if line.strip()]
        encoding = self.enc_combo.currentText().strip() or "utf-8"

        return replace(
            self._base,
            output_dir=output_dir,
            after_action=self.after_combo.currentData() or defaults.after_action,
            max_file_kb=self.max_spin.value(),
            exclude_patterns=excludes,
            fallback_encoding=encoding,
            include_stats=self.stats_cb.isChecked(),
            include_code_map=self.code_map_cb.isChecked(),
            include_binary_map=self.binary_map_cb.isChecked(),
            include_content=self.content_cb.isChecked(),
            theme=self.theme_combo.currentData() or defaults.theme
        )

    def _save_settings(self):
        settings = self._collect_settings()
        save_settings(settings)

        self.save_status.setText("✅ Сохранено")
        self.settings_saved.emit(settings)

    def _browse_output_dir(self):
        current = self.out_dir_edit.text().strip() or AppSettings().output_dir
        path = QFileDialog.getExistingDirectory(self, "Выходная папка", current)

        if path:
            self.out_dir_edit.setText(path)

    def _open_output_dir(self):
        path = Path(self.out_dir_edit.text().strip() or AppSettings().output_dir)
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _new_preset(self):
        raw_name, ok = QInputDialog.getText(self, "Новый пресет", "Имя пресета:")

        if not ok or not raw_name.strip():
            return

        name = save_preset(raw_name, [])
        self._refresh_presets(select=name)

    def _duplicate_preset(self):
        current = self.preset_cb.currentText()

        if not current:
            return

        raw_name, ok = QInputDialog.getText(self, "Дублировать пресет", "Новое имя:", text=f"{current}_copy")

        if not ok or not raw_name.strip():
            return

        name = save_preset(raw_name, self.presets.get(current, []))
        self._refresh_presets(select=name)

    def _delete_preset(self):
        current = self.preset_cb.currentText()

        if not current:
            return

        answer = QMessageBox.question(
            self,
            "Удалить пресет",
            f"Удалить '{current}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        delete_preset(current)
        self._refresh_presets()

    def _save_preset(self):
        current = self.preset_cb.currentText()

        if not current:
            raw_name, ok = QInputDialog.getText(self, "Новый пресет", "Имя пресета:")

            if not ok or not raw_name.strip():
                return

            name = save_preset(raw_name, self._parse_extensions())
        else:
            name = save_preset(current, self._parse_extensions())

        self._refresh_presets(select=name)

    def _import_preset(self):
        path, _ = QFileDialog.getOpenFileName(self, "Импорт пресета", "", "JSON Files (*.json)")

        if not path:
            return

        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            extensions = data.get("extensions", [])

            if not isinstance(extensions, list):
                extensions = []

            name = save_preset(Path(path).stem, extensions)
            self._refresh_presets(select=name)
        except Exception as err:
            QMessageBox.warning(self, "Ошибка импорта", str(err))

    def _export_preset(self):
        current = self.preset_cb.currentText()

        if not current:
            return

        path, _ = QFileDialog.getSaveFileName(self, "Экспорт пресета", f"{current}.json", "JSON Files (*.json)")

        if not path:
            return

        Path(path).write_text(
            json.dumps({"extensions": self.presets.get(current, [])}, indent=2),
            encoding="utf-8"
        )

    def _refresh_presets(self, select: str | None = None):
        presets = load_presets()

        if not presets:
            ensure_default()
            presets = load_presets()

        self.presets = presets
        current = self.preset_cb.currentText()

        self.preset_cb.blockSignals(True)
        self.preset_cb.clear()

        for name in sorted(presets.keys()):
            self.preset_cb.addItem(name)

        if select and select in presets:
            target = select
        elif current in presets:
            target = current
        elif self.preset_cb.count():
            target = self.preset_cb.itemText(0)
        else:
            target = ""

        if target:
            self.preset_cb.setCurrentText(target)

        self.preset_cb.blockSignals(False)
        self._load_preset_extensions()

        self.presets_changed.emit(presets)

    @staticmethod
    def _set_combo_by_data(combo: QComboBox, value: str):
        for i in range(combo.count()):
            if combo.itemData(i) == value:
                combo.setCurrentIndex(i)
                return