# opt
import re
from fnmatch import translate


def normalize_path(path: str) -> str:
    return str(path).replace("\\", "/").strip("/")


class ExclusionMatcher:
    def __init__(self, patterns: list[str]):
        self._names: set[str] = set()
        self._paths: set[str] = set()
        self._globs: list[tuple[re.Pattern, bool]] = []
        for raw in patterns:
            p = normalize_path(str(raw).strip()).rstrip("/")
            if not p:
                continue
            if any(ch in p for ch in "*?["):
                self._globs.append((re.compile(translate(p)), "/" in p))
            elif "/" in p:
                self._paths.add(p)
            else:
                self._names.add(p)

    def matches(self, filename: str) -> bool:
        path = normalize_path(filename)
        if not path:
            return False
        parts = path.split("/")
        if self._names and any(part in self._names for part in parts):
            return True
        for p in self._paths:
            if path == p or path.startswith(p + "/"):
                return True
        for rx, full in self._globs:
            if full:
                if rx.match(path):
                    return True
            elif any(rx.match(part) for part in parts):
                return True
        return False


def is_excluded(filename: str, patterns: list[str]) -> bool:
    return ExclusionMatcher(patterns).matches(filename)