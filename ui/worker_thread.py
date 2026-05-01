from PyQt6.QtCore import QThread, pyqtSignal
from core.extractor import ZipExtractor

class ExtractWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, zip_path: str, out_dir: str, allowed_ext: list[str]):
        super().__init__()
        self.zip_path = zip_path
        self.out_dir = out_dir
        self.allowed_ext = allowed_ext

    def run(self):
        ext = ZipExtractor(self.allowed_ext)
        ok, msg = ext.run(self.zip_path, self.out_dir, self.progress.emit)
        self.finished.emit(ok, msg)