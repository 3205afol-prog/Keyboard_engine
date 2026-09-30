import json
import platform
from pathlib import Path

from core.remapper import Remapper
from core.config_manager import load_config

BASE_DIR = Path(__file__).resolve().parent

with open(BASE_DIR / "layout" / "layout.json", encoding="utf-8") as f:
    layout = json.load(f)

config = load_config()
remapper = Remapper(layout)

system = platform.system()

if system == "Darwin":
    from platforms.mac import run
elif system == "Windows":
    from platforms.windows import run
else:
    raise Exception("Unsupported OS")

run(remapper, config)