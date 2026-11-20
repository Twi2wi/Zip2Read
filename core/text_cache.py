# mod
from collections import OrderedDict
from pathlib import Path


class TextCache:
    def __init__(self, max_items: int = 8, max_bytes: int = 32 * 1024 * 1024):
        self.max_items = max_items
        self.max_bytes = max_bytes
        self._items: OrderedDict[str, tuple[float, int, str]] = OrderedDict()
        self._bytes = 0

    def get(self, path: str) -> str:
        p = Path(path)
        st = p.stat()
        key = str(p)
        entry = self._items.get(key)
        if entry and entry[0] == st.st_mtime and entry[1] == st.st_size:
            self._items.move_to_end(key)
            return entry[2]
        if entry:
            self._drop(key)
        text = p.read_text(encoding="utf-8", errors="replace")
        self._items[key] = (st.st_mtime, st.st_size, text)
        self._bytes += len(text) * 2
        self._trim()
        return text

    def _drop(self, key: str):
        entry = self._items.pop(key, None)
        if entry:
            self._bytes -= len(entry[2]) * 2

    def _trim(self):
        while self._items and (len(self._items) > self.max_items or self._bytes > self.max_bytes):
            _, entry = self._items.popitem(last=False)
            self._bytes -= len(entry[2]) * 2

    def clear(self):
        self._items.clear()
        self._bytes = 0