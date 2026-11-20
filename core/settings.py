# Файл: core/settings.py
import json
from pathlib import Path

from core.models import AppSettings

CONFIG_DIR = Path.home() / ".zip2read"
CONFIG_FILE = CONFIG_DIR / "settings.json"


def load_settings() -> AppSettings:
    defaults = AppSettings()
    if not CONFIG_FILE.exists():
        return defaults

    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return AppSettings.from_dict(data)
    except Exception:
        return defaults


def save_settings(settings: AppSettings) -> AppSettings:
    if not settings.output_dir:
        settings.output_dir = AppSettings().output_dir

    Path(settings.output_dir).mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(settings.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    return settings