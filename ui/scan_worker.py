# mod
from zipfile import ZipFile

from PyQt6.QtCore import QThread, pyqtSignal


class ScanWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str, object)

    def __init__(self, zip_path: str):
        super().__init__()
        self.zip_path = zip_path
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            with ZipFile(self.zip_path, "r") as zf:
                infos = zf.infolist()
                total = len(infos)
                entries = []
                for i, info in enumerate(infos):
                    if self._cancel:
                        self.finished.emit(False, "Отменено", [])
                        return
                    if not info.is_dir():
                        entries.append((info.filename, info.file_size))
                    if i % 200 == 0 or i == total - 1:
                        self.progress.emit(int((i + 1) / max(total, 1) * 100), info.filename)
                entries.sort()
            self.progress.emit(100, "")
            self.finished.emit(True, "", entries)
        except Exception as err:
            self.finished.emit(False, str(err), [])