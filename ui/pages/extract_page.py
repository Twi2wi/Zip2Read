from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QProgressBar, QFileDialog, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

PRESET_COMBO_STYLE = """
QComboBox {
    background: #FFFFFF;
    border: 1px solid #D8C8E8;
    border-radius: 6px;
    padding: 4px 8px;
    color: #2C2430;
    font-size: 11px;
    min-width: 140px;
}
QComboBox:hover { border-color: #FF9E43; }
QComboBox:focus { border-color: #FF9E43; outline: none; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox::down-arrow { image: none; }
QComboBox QAbstractItemView {
    background: #FFFFFF;
    border: 1px solid #D8C8E8;
    selection-background-color: #E6D8FF;
    selection-color: #2C2430;
}
"""

class ExtractPage(QWidget):
    extract_requested = pyqtSignal(str, str)
    open_dir_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.zip_path = None
        self._setup_ui()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 32, 32, 32)
        lay.setSpacing(16)

        title = QLabel("ЭКСТРАКЦИЯ АРХИВА")
        title.setObjectName("section_title")
        lay.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:#D8C8E8; max-height:1px; margin: 0 0 12px 0;")
        lay.addWidget(sep)

        self.drop_lbl = QLabel("📦 Перетащите .zip архив сюда или нажмите «Выбрать архив»")
        self.drop_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_lbl.setObjectName("card")
        self.drop_lbl.setStyleSheet("min-height: 110px;")
        self.drop_lbl.setAcceptDrops(True)
        lay.addWidget(self.drop_lbl)

        ctrl_lay = QHBoxLayout()
        self.btn_browse = QPushButton("Выбрать архив")
        self.btn_browse.setObjectName("add_btn")
        self.btn_browse.clicked.connect(self._browse_zip)
        ctrl_lay.addWidget(self.btn_browse)

        preset_lay = QHBoxLayout()
        preset_lbl = QLabel("Конфигурация:")
        preset_lbl.setObjectName("lang_label")
        preset_lay.addWidget(preset_lbl)
        self.preset_cb = QComboBox()
        # fix: exact style from sys_page.py
        self.preset_cb.setStyleSheet(PRESET_COMBO_STYLE)
        preset_lay.addWidget(self.preset_cb)
        ctrl_lay.addLayout(preset_lay)
        ctrl_lay.addStretch()
        lay.addLayout(ctrl_lay)

        self.btn_extract = QPushButton("Извлечь в Markdown")
        self.btn_extract.setObjectName("connect_btn")
        self.btn_extract.setEnabled(False)
        self.btn_extract.clicked.connect(self._on_extract_click)
        lay.addWidget(self.btn_extract)

        self.progress = QProgressBar()
        self.progress.hide()
        lay.addWidget(self.progress)

        status_lay = QHBoxLayout()
        self.status = QLabel("Готово к работе")
        self.status.setObjectName("section_title")
        status_lay.addWidget(self.status)
        status_lay.addStretch()
        self.btn_open = QPushButton("Открыть папку")
        self.btn_open.setObjectName("add_btn")
        self.btn_open.setEnabled(False)
        self.btn_open.clicked.connect(lambda: self.open_dir_requested.emit())
        status_lay.addWidget(self.btn_open)
        lay.addLayout(status_lay)

        info = QFrame()
        info.setObjectName("card")
        il = QVBoxLayout(info)
        il.setSpacing(6)
        t_lbl = QLabel("📖 КАК ЭТО РАБОТАЕТ")
        t_lbl.setObjectName("card_title")
        t_lbl.setStyleSheet("color: #4A3B52; font-size: 12px; padding: 2px 0; background: transparent;")
        il.addWidget(t_lbl)
        for txt in ["1. Выберите пресет расширений из списка", "2. Перетащите архив или выберите файл", "3. Нажмите «Извлечь» — прогресс отобразится автоматически", "4. Готовый .md появится в Documents/Zip2Read"]:
            l = QLabel(txt)
            l.setStyleSheet("color: #4A3B52; font-size: 12px; padding: 2px 0; background: transparent;")
            il.addWidget(l)
        lay.addWidget(info)
        lay.addStretch()

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls(): e.accept()
        else: e.ignore()

    def dropEvent(self, e: QDropEvent):
        path = e.mimeData().urls()[0].toLocalFile()
        if path.lower().endswith('.zip'): self.set_zip(path)
        else: self.status.setText("⚠️ Требуется .zip архив")

    def set_zip(self, path: str):
        self.zip_path = path
        self.drop_lbl.setText(f"📦 Выбран: {Path(path).name}")
        self.btn_extract.setEnabled(True)

    def update_presets(self, presets: dict):
        self.preset_cb.clear()
        for name in sorted(presets.keys()): self.preset_cb.addItem(name)

    def _browse_zip(self):
        p, _ = QFileDialog.getOpenFileName(self, "Выберите ZIP", "", "ZIP Files (*.zip)")
        if p: self.set_zip(p)

    def _on_extract_click(self):
        if not self.zip_path: return
        self.progress.show()
        self.progress.setValue(0)
        self.extract_requested.emit(self.zip_path, self.preset_cb.currentText())