# mod
from core.sanitize import strip_emoji
from core.report import DumpMeta

class TxtGenerator:
    suffix = ".txt"

    def __init__(self, settings):
        self.settings = settings

    def header(self, meta: DumpMeta) -> str:
        lines = ["архив:"]
        lines.extend(strip_emoji(p) for p in meta.all_paths)
        lines.append("")
        if meta.mode == "all":
            lines.extend(["selected: all", ""])
        else:
            lines.append("selected:")
            groups = meta.grouped_keys()
            if not groups:
                lines.extend(["none", ""])
            for key, paths in groups.items():
                lines.append(strip_emoji(key))
                lines.extend(strip_emoji(p) for p in paths)
                lines.append("")
            if meta.skipped:
                lines.append("skipped:")
                for p, reason in sorted(meta.skipped.items()):
                    lines.append(f"{strip_emoji(p)} {reason}")
                lines.append("")
        return "\n".join(lines) + "\n"

    def entry(self, path: str, content: str | None, status: str) -> str:
        if not self.settings.include_content or status != "ok" or content is None:
            return ""
        body = content if content.endswith("\n") else content + "\n"
        return f"---\n{strip_emoji(path)}\n{body}"

    def footer(self) -> str:
        return "---\n"