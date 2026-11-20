from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget
)
from core.request import ExtractRequest

from core.config_manager import ensure_default, load_presets
from core.settings import load_settings
from themes import get_style
from ui.pages.extract_page import ExtractPage
from ui.pages.info_page import InfoPage
from ui.pages.settings_page import SettingsPage
from ui.pages.md_tools_page import MdToolsPage
from ui.worker_thread import ExtractWorker
from utils.version import __app_name__, __version__


class MainWindow(QMainWindow):
    def __init__(self, settings=None):
        super().__init__()
        self.setWindowTitle(__app_name__)
        self.resize(1040, 700)
        self.setMinimumSize(960, 640)
        # 920, 620

        self.settings = settings or load_settings()
        ensure_default()

        self.presets = load_presets()
        self.worker = None

        self._setup_ui()
        self._apply_settings()
        self._refresh_pages()

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

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFixedHeight(1)
        sep.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sl.addWidget(sep)

        self.nav_btns = []

        for name, idx in [
            ("ЭКСТРАКЦИЯ", 0),
            ("НАСТРОЙКИ", 1),
            ("MARKDOWN", 2),
            ("О ПРИЛОЖЕНИИ", 3),
        ]:
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
        self.settings_page = SettingsPage()
        self.md_tools_page = MdToolsPage()
        self.info_page = InfoPage()

        self.pages.addWidget(self.extract_page)
        self.pages.addWidget(self.settings_page)
        self.pages.addWidget(self.md_tools_page)
        self.pages.addWidget(self.info_page)

        main_lay.addWidget(self.pages)

        self.extract_page.extract_requested.connect(self._start_extract)
        self.extract_page.open_dir_requested.connect(lambda: self._open_directory(Path(self.settings.output_dir)))
        self.extract_page.open_file_requested.connect(self._open_file)
        self.extract_page.cancel_requested.connect(self._cancel_extract)

        self.settings_page.settings_saved.connect(self._on_settings_saved)
        self.settings_page.presets_changed.connect(self._on_presets_changed)

        self.switch_page(0)

    def switch_page(self, idx: int):
        self.pages.setCurrentIndex(idx)

        for i, b in enumerate(self.nav_btns):
            b.setProperty("active", i == idx)
            b.style().unpolish(b)
            b.style().polish(b)

        if idx == 0:
            self.extract_page.update_presets(self.presets)
        elif idx == 1:
            self.settings_page.load(self.settings, self.presets)

    def _apply_settings(self):
        Path(self.settings.output_dir).mkdir(parents=True, exist_ok=True)

        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_style(self.settings.theme))

    def _refresh_pages(self):
        self.extract_page.update_presets(self.presets)
        self.settings_page.load(self.settings, self.presets)

    def _start_extract(self, request: ExtractRequest):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "Обработка", "Извлечение уже выполняется")
            return
        if request.preset_name not in self.presets:
            QMessageBox.warning(self, "Ошибка", "Пресет не найден")
            return
        if not Path(request.zip_path).exists():
            QMessageBox.warning(self, "Ошибка", "Файл архива не найден")
            return
        self.worker = ExtractWorker(
            request,
            self.settings.output_dir,
            self.presets[request.preset_name],
            self.settings
        )
        self.worker.progress.connect(self.extract_page.set_progress)
        self.worker.finished.connect(self._on_finished)
        self.extract_page.set_working()
        self.worker.start()

    def _cancel_extract(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.extract_page.status.setText("Отмена...")

    def _on_finished(self, ok: bool, msg: str):
        output_path = msg if ok else None
        self.extract_page.set_done(ok, msg, output_path)

        if ok:
            path = Path(msg)

            if self.settings.after_action == "open_folder":
                self._open_directory(path.parent)
            elif self.settings.after_action == "open_file":
                self._open_file(path)
        elif msg != "Отменено":
            QMessageBox.warning(self, "Ошибка", msg)

    def _on_settings_saved(self, settings):
        self.settings = settings
        self._apply_settings()
        self._refresh_pages()

    def _on_presets_changed(self, presets: dict):
        self.presets = presets
        self.extract_page.update_presets(presets)

    def _open_file(self, path):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _open_directory(self, path):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def closeEvent(self, event):
        self.extract_page.shutdown()
        self.md_tools_page.shutdown()
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(3000)
        super().closeEvent(event)