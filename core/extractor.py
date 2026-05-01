import zipfile
from pathlib import Path
from datetime import datetime
from typing import List, Callable

BINARY_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.tiff', '.webp', '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.mp3', '.wav', '.ogg', '.exe', '.dll', '.so', '.bin', '.msi', '.dmg', '.deb', '.rpm', '.zip', '.rar', '.7z', '.tar', '.gz', '.obj', '.fbx', '.stl', '.blend', '.pdf', '.docx', '.xlsx', '.pptx', '.iso'}

LANG_MAP = {'.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.html': 'html', '.css': 'css', '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml', '.md': 'markdown', '.cpp': 'cpp', '.c': 'c', '.h': 'cpp', '.hpp': 'cpp', '.java': 'java', '.kt': 'kotlin', '.rs': 'rust', '.go': 'go', '.rb': 'ruby', '.php': 'php', '.sql': 'sql', '.xml': 'xml', '.toml': 'toml', '.sh': 'bash', '.bat': 'batch', '.ps1': 'powershell', '.swift': 'swift', '.lua': 'lua', '.r': 'r', '.tex': 'latex', '.ini': 'ini', '.cfg': 'ini', '.conf': 'ini', '.env': 'bash'}

# opt: anchor generator
def _make_anchor(path: str) -> str:
    return path.replace('/', '-').replace('\\', '-').replace('.', '-').lower()

class ZipExtractor:
    def __init__(self, allowed_ext: List[str]):
        self.allowed_ext = set(allowed_ext)
        self.binary_ext = BINARY_EXT

    def run(self, zip_path: str, out_dir: str, progress_cb: Callable[[int], None]) -> tuple[bool, str]:
        zp = Path(zip_path)
        op = Path(out_dir)
        op.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zp, 'r') as zf:
                entries = [e for e in zf.infolist() if not e.is_dir()]
                total = len(entries)
                code_e, bin_e, other = [], [], []
                lang_counts = {}

                for i, e in enumerate(entries):
                    ext = Path(e.filename).suffix.lower()
                    if ext in self.binary_ext: bin_e.append(e)
                    elif ext in self.allowed_ext:
                        code_e.append(e)
                        lang_counts[LANG_MAP.get(ext, "text")] = lang_counts.get(LANG_MAP.get(ext, "text"), 0) + 1
                    else: other.append(e)
                    progress_cb(int((i + 1) / total * 100))

                total_code = len(code_e)
                pct = round((total_code / total) * 100, 2) if total else 0.0

                # ts added: stats table
                lines = [
                    "---",
                    f"archive_name: {zp.name}",
                    f"extraction_date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    f"total_files: {total}",
                    f"code_percentage: {pct}%",
                    f"code_files: {total_code}",
                    f"binary_files: {len(bin_e)}",
                    f"other_files: {len(other)}",
                    "---\n",
                    "# 📊 Анализ архива",
                    f"- **Код**: {total_code} файлов ({pct}%)",
                    f"- **Бинарные**: {len(bin_e)} файлов",
                    f"- **Прочие**: {len(other)} файлов\n",
                    "# 🌐 Статистика по языкам",
                    "| Язык | Файлов | Доля от кода |",
                    "|---|---|---|"
                ]
                for lang, count in sorted(lang_counts.items(), key=lambda x: x[1], reverse=True):
                    lpct = round((count / total_code) * 100, 2) if total_code else 0.0
                    lines.append(f"| {lang} | {count} | {lpct}% |")

                # ts added: split interactive trees
                lines.extend(["\n# 🗺️ Карта кода"])
                for e in sorted(code_e, key=lambda x: x.filename):
                    a = _make_anchor(e.filename)
                    lines.append(f"- [📄 `{e.filename}`](#{a})")

                lines.extend(["\n# 🗺️ Карта бинарных/прочих файлов"])
                for e in sorted(bin_e + other, key=lambda x: x.filename):
                    a = _make_anchor(e.filename)
                    lines.append(f"- [🗃️ `{e.filename}`](#{a})")

                lines.append("\n# 📦 Содержимое файлов")
                for e in sorted(code_e, key=lambda x: x.filename):
                    ext = Path(e.filename).suffix.lower()
                    lang = LANG_MAP.get(ext, "")
                    a = _make_anchor(e.filename)
                    try:
                        content = zf.read(e.filename).decode('utf-8')
                        lines.extend([f"### <a id=\"{a}\"></a> 📄 `{e.filename}`", f"```{lang}", content, "```\n"])
                    except Exception:
                        lines.extend([f"### <a id=\"{a}\"></a> 📄 `{e.filename}`\n⚠️ *Ошибка чтения/декодирования*\n"])

                out_f = op / f"{zp.stem}_extracted.md"
                out_f.write_text("\n".join(lines), encoding="utf-8")
                return True, str(out_f)
        except Exception as err:
            return False, str(err)