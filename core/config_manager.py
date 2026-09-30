import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.json"

DEFAULT_CONFIG = {
    "startup": {
        "run_on_boot": False,
        "start_minimized": False,
        "minimize_to_tray": False
    },
    "toggle_key": "capslock",
    "block_modifiers": {
        "ctrl": True,
        "alt": True,
        "meta": True
    }
}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return json.loads(json.dumps(DEFAULT_CONFIG))

    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return json.loads(json.dumps(DEFAULT_CONFIG))

    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    merged.update(data)
    merged["startup"] = {**DEFAULT_CONFIG["startup"], **data.get("startup", {})}
    merged["block_modifiers"] = {**DEFAULT_CONFIG["block_modifiers"], **data.get("block_modifiers", {})}
    return merged


def save_config(config: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)