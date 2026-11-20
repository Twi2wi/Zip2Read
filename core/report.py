# mod
from dataclasses import dataclass, field


@dataclass
class DumpMeta:
    archive_name: str
    total_files: int = 0
    excluded_files: int = 0
    mode: str = "all"
    all_paths: list[str] = field(default_factory=list)
    excluded_paths: set[str] = field(default_factory=set)
    code_paths: list[str] = field(default_factory=list)
    binary_paths: list[str] = field(default_factory=list)
    other_paths: list[str] = field(default_factory=list)
    lang_counts: dict[str, int] = field(default_factory=dict)
    selected: list[str] = field(default_factory=list)
    dumped: list[str] = field(default_factory=list)
    keys: dict[str, list[str]] = field(default_factory=dict)
    skipped: dict[str, str] = field(default_factory=dict)
    errors: set[str] = field(default_factory=set)
    large: set[str] = field(default_factory=set)

    def grouped_keys(self) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = {}
        for path in self.selected:
            for key in self.keys.get(path, []):
                groups.setdefault(key, []).append(path)
        return {k: groups[k] for k in sorted(groups)}

    def code_percent(self) -> float:
        considered = max(self.total_files - self.excluded_files, 0)
        return round(len(self.code_paths) / considered * 100, 2) if considered else 0.0

    def sort(self):
        self.all_paths.sort()
        self.code_paths.sort()
        self.binary_paths.sort()
        self.other_paths.sort()
        self.selected.sort()
        self.dumped.sort()