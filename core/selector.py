# mod
import re
from dataclasses import dataclass, field


def normalize_path(path: str) -> str:
    return str(path).replace("\\", "/").strip("/")


@dataclass
class Selection:
    selected: bool = False
    keys: list[str] = field(default_factory=list)


class FileSelector:
    MODES = ("all", "folder", "file", "content")

    def __init__(
        self,
        mode: str = "all",
        folders: list[str] | None = None,
        files: list[str] | None = None,
        query: str = "",
        is_regex: bool = False,
        case_sensitive: bool = False,
    ):
        self.mode = mode if mode in self.MODES else "all"
        self.folders = sorted({normalize_path(f) for f in (folders or []) if normalize_path(f)})
        self.files = {normalize_path(f) for f in (files or []) if normalize_path(f)}
        self.query = query or ""
        self.is_regex = is_regex
        self.case_sensitive = case_sensitive
        self._rx: re.Pattern | None = None
        self._needle = ""
        if self.mode == "content" and self.query:
            flags = 0 if case_sensitive else re.IGNORECASE
            if is_regex:
                try:
                    self._rx = re.compile(self.query, flags)
                except re.error as err:
                    raise ValueError(f"Некорректный regex: {err}") from err
            else:
                self._needle = self.query if case_sensitive else self.query.lower()

    def needs_content(self) -> bool:
        return self.mode == "content" and bool(self.query)

    def config_error(self) -> str | None:
        if self.mode == "folder" and not self.folders:
            return "Не выбрана ни одна папка"
        if self.mode == "file" and not self.files:
            return "Не выбран ни один файл"
        if self.mode == "content" and not self.query:
            return "Пустой поисковый запрос"
        return None

    def match(self, path: str, content: str | None = None) -> Selection:
        path = normalize_path(path)
        if self.mode == "all":
            return Selection(True, [])
        if self.mode == "folder":
            keys = [
                f"folder: {f}"
                for f in self.folders
                if path == f or path.startswith(f + "/")
            ]
            return Selection(bool(keys), keys)
        if self.mode == "file":
            if path in self.files:
                return Selection(True, [f"file: {path}"])
            return Selection(False, [])
        if self.mode == "content":
            if not self.query or content is None:
                return Selection(False, [])
            if self._rx is not None:
                found = self._rx.search(content) is not None
            else:
                hay = content if self.case_sensitive else content.lower()
                found = self._needle in hay
            return Selection(found, [f"search: {self.query}"] if found else [])
        return Selection(False, [])