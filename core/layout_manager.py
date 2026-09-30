import json
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LAYOUT_FILE = BASE_DIR / "layout" / "layout.json"
PRESETS_DIR = BASE_DIR / "layout" / "presets"

BUILTIN_IDS = ["default", "onishi"]
BUILTIN_NAMES = {
    "default": "初期値",
    "onishi": "大西配列",
}

# 編集・変換対象として許可するキー一覧（数字・他記号は無効）
EDITABLE_KEYS = list("abcdefghijklmnopqrstuvwxyz") + [";", ",", ".", "/", "-"]

ONISHI_LAYOUT = {
    "w": "l", "e": "u", "r": ",", "t": ".", "y": "f", "u": "w", "i": "r", "o": "y",
    "a": "e", "s": "i", "d": "a", "f": "o", "g": "-", "h": "k", "j": "t", "k": "n",
    "l": "s", ";": "h",
    "b": ";", "n": "g", "m": "d", ",": "m", ".": "j", "/": "b",
    "-": "/",
}


def _ensure_dirs():
    PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    LAYOUT_FILE.parent.mkdir(parents=True, exist_ok=True)


def _ensure_builtin_presets():
    _ensure_dirs()
    default_path = PRESETS_DIR / "default.json"
    if not default_path.exists():
        save_preset("default", {})

    onishi_path = PRESETS_DIR / "onishi.json"
    if not onishi_path.exists():
        save_preset("onishi", ONISHI_LAYOUT)


def list_presets() -> list[dict]:
    """[{id, name, is_builtin}, ...] を返す。組み込み2種を先頭に固定。"""
    _ensure_builtin_presets()

    result = []
    for pid in BUILTIN_IDS:
        result.append({"id": pid, "name": BUILTIN_NAMES[pid], "is_builtin": True})

    for path in sorted(PRESETS_DIR.glob("*.json")):
        pid = path.stem
        if pid in BUILTIN_IDS:
            continue
        data = _read_json(path)
        name = data.get("_meta", {}).get("name", pid)
        result.append({"id": pid, "name": name, "is_builtin": False})

    return result


def _read_json(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def load_preset(preset_id: str) -> dict:
    """変換マッピングのみを返す（_metaは除く）"""
    path = PRESETS_DIR / f"{preset_id}.json"
    data = _read_json(path)
    return {k: v for k, v in data.items() if k != "_meta"}


def save_preset(preset_id: str, mapping: dict, name: str | None = None):
    _ensure_dirs()
    path = PRESETS_DIR / f"{preset_id}.json"

    data = dict(mapping)
    if name is not None:
        data["_meta"] = {"name": name}
    elif preset_id in BUILTIN_NAMES:
        data["_meta"] = {"name": BUILTIN_NAMES[preset_id]}

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def delete_preset(preset_id: str):
    if preset_id in BUILTIN_IDS:
        raise ValueError("組み込みプリセットは削除できません")
    path = PRESETS_DIR / f"{preset_id}.json"
    if path.exists():
        path.unlink()


def generate_preset_id() -> str:
    """新規タブ用のユニークID"""
    import time
    return f"user_{int(time.time() * 1000)}"


def get_active_layout() -> dict:
    """現在エンジンが使っている layout.json の内容"""
    if not LAYOUT_FILE.exists():
        return {}
    return _read_json(LAYOUT_FILE)


def apply_preset_as_active(mapping: dict):
    """指定内容を layout.json（実行中レイアウト）として書き出す"""
    _ensure_dirs()
    with open(LAYOUT_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)


def layout_hash(mapping: dict) -> str:
    """内容比較用（辞書の順序に依存しないハッシュ）"""
    normalized = json.dumps(mapping, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def find_active_preset_id() -> str | None:
    """現在の layout.json と内容が一致するプリセットIDを探す"""
    active = get_active_layout()
    active_hash = layout_hash(active)

    for info in list_presets():
        mapping = load_preset(info["id"])
        if layout_hash(mapping) == active_hash:
            return info["id"]
    return None