# mod
import re
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from core.md_analysis import FileHits, Hit, analyze, extract
from core.sanitize import strip_emoji

MAX_HITS = 20000
SNIPPET = 160


class _Cancelled(Exception):
    pass


class MdToolsWorker(QThread):
    progress = pyqtSignal(int, str)
    done = pyqtSignal(bool, str, object)

    def __init__(self, op: str, files: list[str], params: dict):
        super().__init__()
        self.op = op
        self.files = files
        self.params = params
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def _check(self):
        if self._cancel:
            raise _Cancelled()

    def _tick(self, index: int, path: str):
        self._check()
        self.progress.emit(int(index / max(len(self.files), 1) * 100), Path(path).name)

    def _read(self, path: str) -> str | None:
        try:
            return Path(path).read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None

    def run(self):
        try:
            if self.op == "search":
                payload = self._search()
            elif self.op == "stats":
                payload = self._stats()
            elif self.op == "extract":
                payload = self._extract()
            elif self.op == "merge":
                payload = self._merge()
            else:
                self.done.emit(False, "Неизвестная операция", None)
                return
            self.progress.emit(100, "")
            self.done.emit(True, "", payload)
        except _Cancelled:
            self.done.emit(False, "Отменено", None)
        except Exception as err:
            self.done.emit(False, str(err), None)

    def _search(self):
        pattern = self.params["pattern"]
        flags = 0 if self.params["case"] else re.IGNORECASE
        rx = re.compile(pattern if self.params["regex"] else re.escape(pattern), flags)
        result: list[FileHits] = []
        total = 0
        truncated = False
        for index, path in enumerate(self.files):
            self._tick(index, path)
            text = self._read(path)
            if text is None:
                continue
            hits: list[Hit] = []
            for i, line in enumerate(text.splitlines()):
                if i % 2000 == 0:
                    self._check()
                for m in rx.finditer(line):
                    if total >= MAX_HITS:
                        truncated = True
                        break
                    snippet = line.strip()
                    if len(snippet) > SNIPPET:
                        snippet = snippet[:SNIPPET] + "…"
                    hits.append(Hit(i, m.start(), m.end(), snippet))
                    total += 1
                if truncated:
                    break
            if hits:
                result.append(FileHits(path, hits))
            if truncated:
                break
        return {"files": result, "total": total, "truncated": truncated}

    def _stats(self):
        rows = []
        for index, path in enumerate(self.files):
            self._tick(index, path)
            text = self._read(path)
            if text is None:
                continue
            rows.append(analyze(path, text))
        return rows

    def _extract(self):
        kind = self.params["kind"]
        parts = []
        count = 0
        for index, path in enumerate(self.files):
            self._tick(index, path)
            text = self._read(path)
            if text is None:
                continue
            items = extract(text, kind)
            if items:
                count += len(items)
                parts.append(f"## {Path(path).name}\n\n" + "\n\n".join(items))
            self._check()
        return {"text": strip_emoji("\n\n".join(parts)), "count": count}

    def _merge(self):
        sep = self.params["sep"]
        parts = []
        for index, path in enumerate(self.files):
            self._tick(index, path)
            text = self._read(path)
            if text is None:
                continue
            if sep:
                parts.append(f"\n\n---\n\n# {Path(path).name}\n\n")
            parts.append(text)
            self._check()
        return {"text": strip_emoji("".join(parts)), "count": len(self.files)}