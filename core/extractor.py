# mod
import tempfile
from pathlib import Path
from typing import Callable
from zipfile import ZipFile

from core.exclusions import ExclusionMatcher
from core.languages import BINARY_EXT, LANG_MAP
from core.markdown_generator import MarkdownGenerator
from core.models import AppSettings
from core.report import DumpMeta
from core.sanitize import strip_emoji
from core.selector import FileSelector
from core.txt_generator import TxtGenerator

CHUNK = 256 * 1024


class _Cancelled(Exception):
    pass


class ZipExtractor:
    def __init__(self, allowed_ext: list[str], settings: AppSettings, selector: FileSelector | None = None):
        self.allowed_ext = {str(ext).lower() for ext in allowed_ext}
        self.settings = settings
        self.selector = selector or FileSelector(
            mode=settings.extract_mode,
            folders=settings.selected_folders,
            files=settings.selected_files,
            query=settings.content_query,
            is_regex=settings.content_is_regex,
            case_sensitive=settings.content_case_sensitive
        )

    def run(
        self,
        zip_path: str,
        out_dir: str,
        progress_cb: Callable[[int, str], None],
        cancel_cb: Callable[[], bool] | None = None
    ) -> tuple[bool, str]:
        zp = Path(zip_path)
        op = Path(out_dir)
        op.mkdir(parents=True, exist_ok=True)
        err = self.selector.config_error()
        if err:
            return False, err

        gen = TxtGenerator(self.settings) if self.settings.output_format == "txt" else MarkdownGenerator(self.settings)
        out_f = op / f"{zp.stem}_extracted{gen.suffix}"
        tmp_path: Path | None = None
        started = False
        try:
            with ZipFile(zp, "r") as zf:
                entries = [e for e in zf.infolist() if not e.is_dir()]
                total = len(entries)
                meta = DumpMeta(archive_name=zp.name, total_files=total, mode=self.selector.mode)
                matcher = ExclusionMatcher(self.settings.exclude_patterns)
                max_bytes = self.settings.max_file_kb * 1024 if self.settings.max_file_kb > 0 else 0

                tmp = tempfile.NamedTemporaryFile(
                    "w+", encoding="utf-8", newline="\n",
                    dir=op, prefix="zip2read_", suffix=".part", delete=False
                )
                tmp_path = Path(tmp.name)
                with tmp:
                    for index, entry in enumerate(entries):
                        if cancel_cb and cancel_cb():
                            raise _Cancelled()
                        path = entry.filename
                        meta.all_paths.append(path)
                        progress_cb(int(index / max(total, 1) * 95), path)
                        if matcher.matches(path):
                            meta.excluded_files += 1
                            meta.excluded_paths.add(path)
                            continue
                        ext = Path(path).suffix.lower()
                        if ext in BINARY_EXT:
                            meta.binary_paths.append(path)
                            kind = "binary"
                        elif ext in self.allowed_ext:
                            meta.code_paths.append(path)
                            lang = LANG_MAP.get(ext, "text")
                            meta.lang_counts[lang] = meta.lang_counts.get(lang, 0) + 1
                            kind = "code"
                        else:
                            meta.other_paths.append(path)
                            kind = "other"
                        self._handle(zf, entry, kind, meta, gen, tmp, max_bytes, cancel_cb)

                meta.sort()
                progress_cb(96, "Сборка дампа")
                started = True
                with out_f.open("w", encoding="utf-8", newline="\n") as out:
                    out.write(gen.header(meta))
                    with tmp_path.open("r", encoding="utf-8", newline="") as body:
                        while True:
                            if cancel_cb and cancel_cb():
                                raise _Cancelled()
                            block = body.read(CHUNK)
                            if not block:
                                break
                            out.write(block)
                    if meta.dumped:
                        out.write(gen.footer())
                progress_cb(100, "")
                return True, str(out_f)
        except _Cancelled:
            if started:
                out_f.unlink(missing_ok=True)
            return False, "Отменено"
        except Exception as err:
            if started:
                out_f.unlink(missing_ok=True)
            return False, str(err)
        finally:
            if tmp_path:
                tmp_path.unlink(missing_ok=True)

    def _handle(self, zf, entry, kind, meta, gen, tmp, max_bytes, cancel_cb):
        path = entry.filename
        need = self.selector.needs_content()
        text = None
        status = "ok"

        if need:
            if kind != "code":
                return
            if max_bytes and entry.file_size > max_bytes:
                meta.large.add(path)
                return
            text, status = self._read_text(zf, entry, cancel_cb)
            if status == "error":
                meta.errors.add(path)
            sel = self.selector.match(path, text if status == "ok" else None)
            if not sel.selected:
                return
        else:
            sel = self.selector.match(path)
            if not sel.selected:
                return

        if self.selector.mode != "all":
            meta.selected.append(path)
            meta.keys[path] = sel.keys

        if kind != "code":
            meta.skipped[path] = "бинарный" if kind == "binary" else "прочий"
            return

        if not self.settings.include_content and not need:
            return

        if not need:
            if max_bytes and entry.file_size > max_bytes:
                meta.large.add(path)
                meta.skipped[path] = "размер"
                tmp.write(gen.entry(path, None, "large"))
                return
            text, status = self._read_text(zf, entry, cancel_cb)

        if status == "error":
            meta.skipped[path] = "ошибка чтения"
            tmp.write(gen.entry(path, None, "error"))
            return

        if not self.settings.include_content:
            return

        meta.dumped.append(path)
        tmp.write(gen.entry(path, strip_emoji(text), "ok"))

    def _read_text(self, zf, entry, cancel_cb) -> tuple[str | None, str]:
        try:
            chunks = []
            with zf.open(entry, "r") as stream:
                while True:
                    if cancel_cb and cancel_cb():
                        raise _Cancelled()
                    block = stream.read(CHUNK)
                    if not block:
                        break
                    chunks.append(block)
            raw = b"".join(chunks)
        except _Cancelled:
            raise
        except Exception:
            return None, "error"
        return self._decode(raw), "ok"

    def _decode(self, raw: bytes) -> str:
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            pass
        try:
            return raw.decode(self.settings.fallback_encoding, errors="replace")
        except Exception:
            return raw.decode("utf-8", errors="replace")