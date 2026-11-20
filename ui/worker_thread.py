# fix
from dataclasses import replace

from PyQt6.QtCore import QThread, pyqtSignal

from core.extractor import ZipExtractor
from core.models import AppSettings
from core.request import ExtractRequest


class ExtractWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, request: ExtractRequest, out_dir: str, allowed_ext: list[str], settings: AppSettings):
        super().__init__()
        self.request = request
        self.out_dir = out_dir
        self.allowed_ext = allowed_ext
        self.settings = settings
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        settings = replace(self.settings, output_format=self.request.output_format)
        extractor = ZipExtractor(self.allowed_ext, settings, self.request.selector)
        ok, msg = extractor.run(
            self.request.zip_path,
            self.out_dir,
            self.progress.emit,
            lambda: self._cancel
        )
        self.finished.emit(ok, msg)