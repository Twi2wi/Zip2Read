# mod
import os
from pathlib import Path
from urllib.parse import unquote

from PyQt6.QtCore import QMimeData, QUrl

ZIP_MAGIC = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
WIN_FORMATS = (
    'application/x-qt-windows-mime;value="FileNameW"',
    'application/x-qt-windows-mime;value="FileName"'
)


def _clean(raw: str) -> str:
    text = raw.replace("\x00", "").strip().strip('"').strip("'").strip()
    if not text:
        return ""
    return os.path.normpath(os.path.expanduser(text))


def _from_url(url: QUrl) -> str:
    if url.isLocalFile():
        return _clean(url.toLocalFile())
    if url.scheme() in ("", "file"):
        path = unquote(url.path() or url.toString())
        if len(path) > 2 and path[0] == "/" and path[1].isalpha() and path[2] == ":":
            path = path[1:]
        return _clean(path)
    return ""


def _decode(raw: bytes, wide: bool) -> str:
    if wide:
        return raw.decode("utf-16-le", errors="replace")
    try:
        return raw.decode("mbcs", errors="replace")
    except LookupError:
        return raw.decode("latin-1", errors="replace")


def candidate_paths(mime: QMimeData | None) -> list[str]:
    if mime is None:
        return []
    paths: list[str] = []
    seen: set[str] = set()

    def push(value: str):
        if value and value not in seen:
            seen.add(value)
            paths.append(value)

    if mime.hasUrls():
        for url in mime.urls():
            push(_from_url(url))
    if mime.hasFormat("text/uri-list"):
        raw = bytes(mime.data("text/uri-list")).decode("utf-8", errors="replace")
        for line in raw.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                push(_from_url(QUrl(line)))
    if mime.hasText():
        for line in mime.text().splitlines():
            push(_clean(line))
    for fmt in WIN_FORMATS:
        if mime.hasFormat(fmt):
            push(_clean(_decode(bytes(mime.data(fmt)), fmt.endswith('FileNameW"'))))
    return paths


def is_zip_file(path: str) -> bool:
    p = Path(path)
    try:
        if not p.is_file():
            return False
        if p.suffix.lower() == ".zip":
            return True
        with p.open("rb") as f:
            return f.read(4) in ZIP_MAGIC
    except OSError:
        return False


def pick_zip(mime: QMimeData | None) -> str | None:
    return next((p for p in candidate_paths(mime) if is_zip_file(p)), None)


def accepts_mime(mime: QMimeData | None) -> bool:
    if mime is None:
        return False
    if mime.hasUrls() or mime.hasText() or mime.hasFormat("text/uri-list"):
        return True
    return any(mime.hasFormat(f) for f in WIN_FORMATS)