# Файл: core/config_manager.py
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PRESETS_DIR = BASE_DIR / "presets"
PRESETS_DIR.mkdir(exist_ok=True)

DEFAULT_EXTENSIONS = [
    ".py", ".js", ".ts", ".html", ".css", ".json", ".hjson",
    ".yaml", ".yml", ".md", ".cpp", ".c", ".h", ".java",
    ".rs", ".go", ".sh", ".sql", ".xml", ".toml", ".lua",
    ".vert", ".frag"
]


def sanitize_name(name: str) -> str:
    clean = str(name).strip().replace("/", "_").replace("\\", "_")
    return clean or "preset"


def preset_path(name: str) -> Path:
    return PRESETS_DIR / f"{sanitize_name(name)}.json"


def ensure_default():
    path = PRESETS_DIR / "default.json"
    if not path.exists():
        save_preset("default", DEFAULT_EXTENSIONS)


def load_presets() -> dict[str, list[str]]:
    result = {}

    for file in sorted(PRESETS_DIR.glob("*.json")):
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            extensions = data.get("extensions", [])

            if not isinstance(extensions, list):
                continue

            result[file.stem] = [str(ext).lower() for ext in extensions]
        except Exception:
            continue

    return result


def save_preset(name: str, extensions: list[str]) -> str:
    clean_name = sanitize_name(name)
    clean_extensions = []

    for ext in extensions:
        ext = str(ext).strip().lower()
        if not ext:
            continue

        if not ext.startswith("."):
            ext = f".{ext}"

        if ext not in clean_extensions:
            clean_extensions.append(ext)

    path = PRESETS_DIR / f"{clean_name}.json"
    path.write_text(
        json.dumps({"extensions": clean_extensions}, indent=2),
        encoding="utf-8"
    )

    return clean_name


def delete_preset(name: str):
    preset_path(name).unlink(missing_ok=True)