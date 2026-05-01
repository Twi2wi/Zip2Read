from pathlib import Path
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QStackedWidget, QPushButton, QLabel, QMessageBox, QSizePolicy
from PyQt6.QtCore import Qt
from ui.worker_thread import ExtractWorker
from core.config_manager import load_presets, ensure_default
from ui.pages.extract_page import ExtractPage
from ui.pages.info_page import InfoPage
from utils.version import __version__, __app_name__
import subprocess

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(__app_name__)
        self.resize(880, 580)
        self.out_dir = Path.home() / "Documents" / "Zip2Read"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        ensure_default()
        self.presets = {}
        self._setup_ui()
        self._load_presets()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_lay = QHBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)

        logo = QLabel(__app_name__.upper())
        logo.setObjectName("logo_label")
        sl.addWidget(logo)
        ver = QLabel(f"v{__version__}")
        ver.setObjectName("version_label")
        sl.addWidget(ver)

        # fix: separator stretch & background
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #D8C8E8;")
        sep.setFixedHeight(1)
        sep.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sl.addWidget(sep)

        self.nav_btns = []
        for name, idx in [("ЭКСТРАКЦИЯ", 0), ("О ПРИЛОЖЕНИИ", 1)]:
            b = QPushButton(name)
            b.setObjectName("nav_btn")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _, i=idx: self.switch_page(i))
            sl.addWidget(b)
            self.nav_btns.append(b)

        sl.addStretch()
        main_lay.addWidget(sidebar)

        self.pages = QStackedWidget()
        self.extract_page = ExtractPage()
        self.info_page = InfoPage()
        self.pages.addWidget(self.extract_page)
        self.pages.addWidget(self.info_page)
        main_lay.addWidget(self.pages)

        self.extract_page.extract_requested.connect(self._start_extract)
        self.extract_page.open_dir_requested.connect(self._open_dir)
        self.switch_page(0)

    def switch_page(self, idx: int):
        self.pages.setCurrentIndex(idx)
        for i, b in enumerate(self.nav_btns):
            b.setProperty("active", i == idx)
            b.style().unpolish(b)
            b.style().polish(b)
        if idx == 0: self.extract_page.update_presets(self.presets)

    def _load_presets(self):
        self.presets = load_presets()
        self.extract_page.update_presets(self.presets)

    def _start_extract(self, zip_path: str, preset_name: str):
        if preset_name not in self.presets: return
        self.extract_page.btn_extract.setEnabled(False)
        self.extract_page.btn_open.setEnabled(False)
        self.extract_page.progress.setValue(0)
        self.extract_page.status.setText("Обработка...")

        self.worker = ExtractWorker(zip_path, str(self.out_dir), self.presets[preset_name])
        self.worker.progress.connect(self.extract_page.progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_finished(self, ok: bool, msg: str):
        self.extract_page.progress.hide()
        self.extract_page.btn_extract.setEnabled(True)
        if ok:
            self.extract_page.status.setText("✅ Успешно")
            self.extract_page.btn_open.setEnabled(True)
            QMessageBox.information(self, "Готово", f"Файл сохранён в:\n{msg}")
        else:
            self.extract_page.status.setText("❌ Ошибка")
            QMessageBox.warning(self, "Ошибка", msg)

    def _open_dir(self):
        if self.out_dir.exists():
            subprocess.Popen(f'explorer "{self.out_dir}"')