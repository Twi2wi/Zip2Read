import json
from pathlib import Path

PRESETS_DIR = Path("presets")
PRESETS_DIR.mkdir(exist_ok=True)

def ensure_default():
    p = PRESETS_DIR / "default.json"
    if not p.exists():
        p.write_text(json.dumps({
            "extensions": [".py", ".js", ".ts", ".html", ".css", ".json", ".yaml", ".yml", ".md", ".cpp", ".c", ".h", ".java", ".rs", ".go", ".sh", ".sql", ".xml", ".toml", ".lua"]
        }, indent=2), encoding="utf-8")

def load_presets() -> dict[str, list[str]]:
    res = {}
    for f in PRESETS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            res[f.stem] = data.get("extensions", [])
        except Exception:
            pass
    return res