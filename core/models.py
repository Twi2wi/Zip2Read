# mod
from dataclasses import dataclass, field
from pathlib import Path


def default_output_dir() -> str:
    return str(Path.home() / "Documents" / "Zip2Read")


def default_excludes() -> list[str]:
    return [
        ".git",
        "node_modules",
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "dist",
        "build",
        ".venv",
        "venv"
    ]


OUTPUT_FORMATS = ("md", "txt")
EXTRACT_MODES = ("all", "folder", "file", "content")


@dataclass
class AppSettings:
    output_dir: str = field(default_factory=default_output_dir)
    after_action: str = "open_folder"
    max_file_kb: int = 512
    exclude_patterns: list[str] = field(default_factory=default_excludes)
    fallback_encoding: str = "cp1251"
    include_stats: bool = True
    include_code_map: bool = True
    include_binary_map: bool = True
    include_content: bool = True
    theme: str = "light"
    output_format: str = "md"
    extract_mode: str = "all"
    content_query: str = ""
    content_is_regex: bool = False
    content_case_sensitive: bool = False
    selected_folders: list[str] = field(default_factory=list)
    selected_files: list[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "output_dir": self.output_dir,
            "after_action": self.after_action,
            "max_file_kb": self.max_file_kb,
            "exclude_patterns": self.exclude_patterns,
            "fallback_encoding": self.fallback_encoding,
            "include_stats": self.include_stats,
            "include_code_map": self.include_code_map,
            "include_binary_map": self.include_binary_map,
            "include_content": self.include_content,
            "theme": self.theme,
            "output_format": self.output_format,
            "extract_mode": self.extract_mode,
            "content_query": self.content_query,
            "content_is_regex": self.content_is_regex,
            "content_case_sensitive": self.content_case_sensitive
        }

    @classmethod
    def from_dict(cls, data: dict):
        base = cls()
        fmt = str(data.get("output_format", base.output_format))
        mode = str(data.get("extract_mode", base.extract_mode))
        return cls(
            output_dir=str(data.get("output_dir", base.output_dir) or base.output_dir),
            after_action=str(data.get("after_action", base.after_action) or base.after_action),
            max_file_kb=int(data.get("max_file_kb", base.max_file_kb)),
            exclude_patterns=list(data.get("exclude_patterns", base.exclude_patterns)),
            fallback_encoding=str(data.get("fallback_encoding", base.fallback_encoding) or base.fallback_encoding),
            include_stats=bool(data.get("include_stats", base.include_stats)),
            include_code_map=bool(data.get("include_code_map", base.include_code_map)),
            include_binary_map=bool(data.get("include_binary_map", base.include_binary_map)),
            include_content=bool(data.get("include_content", base.include_content)),
            theme=str(data.get("theme", base.theme) or base.theme),
            output_format=fmt if fmt in OUTPUT_FORMATS else base.output_format,
            extract_mode=mode if mode in EXTRACT_MODES else base.extract_mode,
            content_query=str(data.get("content_query", "")),
            content_is_regex=bool(data.get("content_is_regex", False)),
            content_case_sensitive=bool(data.get("content_case_sensitive", False))
        )