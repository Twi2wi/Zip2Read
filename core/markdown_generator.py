# mod
import re
from datetime import datetime
from pathlib import Path

from core.languages import LANG_MAP
from core.report import DumpMeta
from core.sanitize import strip_emoji

_BACKTICKS = re.compile(r"`{3,}")


def _make_anchor(path: str) -> str:
    return path.replace("/", "-").replace("\\", "-").replace(".", "-").lower()


def _fence(content: str) -> str:
    longest = 0
    for m in _BACKTICKS.finditer(content):
        longest = max(longest, len(m.group(0)))
    return "`" * max(3, longest + 1)


class MarkdownGenerator:
    suffix = ".md"

    def __init__(self, settings):
        self.settings = settings

    def header(self, meta: DumpMeta) -> str:
        s = self.settings
        pct = meta.code_percent()
        total_code = len(meta.code_paths)
        lines = [
            "---",
            f"archive_name: {strip_emoji(meta.archive_name)}",
            f"extraction_date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"total_files: {meta.total_files}",
            f"excluded_files: {meta.excluded_files}",
            f"code_percentage: {pct}%",
            f"code_files: {total_code}",
            f"binary_files: {len(meta.binary_paths)}",
            f"other_files: {len(meta.other_paths)}",
            f"extract_mode: {meta.mode}",
            f"dumped_files: {len(meta.dumped)}",
            "---",
            ""
        ]
        if s.include_stats:
            lines.extend([
                "# Анализ архива",
                f"- **Код**: {total_code} файлов ({pct}%)",
                f"- **Бинарные**: {len(meta.binary_paths)} файлов",
                f"- **Прочие**: {len(meta.other_paths)} файлов",
                f"- **Исключено**: {meta.excluded_files} файлов",
                f"- **В дампе**: {len(meta.dumped)} файлов",
                "",
                "# Статистика по языкам",
                "| Язык | Файлов | Доля от кода |",
                "|---|---|---|"
            ])
            for lang, count in sorted(meta.lang_counts.items(), key=lambda i: i[1], reverse=True):
                share = round(count / total_code * 100, 2) if total_code else 0.0
                lines.append(f"| {lang} | {count} | {share}% |")
            lines.append("")

        marks: dict[str, str] = {}
        for p in meta.binary_paths:
            marks[p] = "бинарный"
        for p in meta.other_paths:
            marks[p] = "прочий"
        for p in meta.large:
            marks[p] = "пропущен: размер"
        for p in meta.errors:
            marks[p] = "ошибка чтения"
        for p in meta.excluded_paths:
            marks[p] = "исключён"

        lines.append("# Полный список файлов")
        for p in meta.all_paths:
            note = marks.get(p)
            lines.append(f"- `{strip_emoji(p)}`" + (f" — {note}" if note else ""))
        lines.append("")

        lines.append("# Выбранные файлы")
        if meta.mode == "all":
            lines.extend(["Режим: весь архив (кроме исключений)", ""])
        else:
            groups = meta.grouped_keys()
            if not groups:
                lines.extend(["Ничего не выбрано", ""])
            for key, paths in groups.items():
                lines.append(f"## {strip_emoji(key)}")
                for p in paths:
                    lines.append(f"- `{strip_emoji(p)}`")
                lines.append("")
            if meta.skipped:
                lines.append("## Пропущено")
                for p, reason in sorted(meta.skipped.items()):
                    lines.append(f"- `{strip_emoji(p)}` — {reason}")
                lines.append("")

        dumped = set(meta.dumped)
        if s.include_code_map:
            lines.append("# Карта кода")
            for p in meta.code_paths:
                sp = strip_emoji(p)
                if s.include_content and p in dumped:
                    lines.append(f"- [`{sp}`](#{_make_anchor(p)})")
                else:
                    lines.append(f"- `{sp}`")
            lines.append("")
        if s.include_binary_map:
            lines.append("# Карта бинарных/прочих файлов")
            for p in sorted(meta.binary_paths + meta.other_paths):
                lines.append(f"- `{strip_emoji(p)}`")
            lines.append("")
        if s.include_content:
            lines.extend(["# Содержимое файлов", ""])
        return "\n".join(lines) + "\n"

    def entry(self, path: str, content: str | None, status: str) -> str:
        if not self.settings.include_content:
            return ""
        lang = LANG_MAP.get(Path(path).suffix.lower(), "")
        head = f"### <a id=\"{_make_anchor(path)}\"></a> `{strip_emoji(path)}`\n\n"
        if status == "error":
            return head + "*Ошибка чтения/декодирования*\n\n"
        if status == "large":
            return head + "*Файл пропущен: превышен лимит размера*\n\n"
        if content is None:
            return head + "*Содержимое недоступно*\n\n"
        fence = _fence(content)
        body = content if content.endswith("\n") else content + "\n"
        return f"{head}{fence}{lang}\n{body}{fence}\n\n"

    def footer(self) -> str:
        return ""