import subprocess
import sys
from pathlib import Path

TASK_NAME = "KeyboardEngineAutostart"
LEGACY_REG_NAME = "KeyboardEngine"  # 旧レジストリ方式の値名

BASE_DIR = Path(__file__).resolve().parent.parent
MAIN_SCRIPT = BASE_DIR / "main.py"


def _startup_command() -> str:
    from core.config_manager import load_config

    python_exe = Path(sys.executable)
    pythonw = python_exe.parent / "pythonw.exe"
    exe = pythonw if pythonw.exists() else python_exe

    cmd = f'"{exe}" "{MAIN_SCRIPT}" --autostart'
    if load_config()["startup"]["start_minimized"]:
        cmd += " --minimized"
    return cmd


def _cleanup_legacy_registry_entry():
    """過去のレジストリ方式(Run キー)の登録が残っていれば削除する"""
    import winreg

    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(
                hive,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY,
            ) as key:
                winreg.DeleteValue(key, LEGACY_REG_NAME)
        except OSError:
            pass


def is_startup_enabled() -> bool:
    result = subprocess.run(
        ["schtasks", "/query", "/tn", TASK_NAME],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def set_startup_enabled(enabled: bool):
    _cleanup_legacy_registry_entry()

    if enabled:
        result = subprocess.run(
            [
                "schtasks", "/create",
                "/tn", TASK_NAME,
                "/tr", _startup_command(),
                "/sc", "onlogon",
                "/rl", "highest",
                "/f",
            ],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)
    else:
        result = subprocess.run(
            ["schtasks", "/delete", "/tn", TASK_NAME, "/f"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            combined = result.stdout + result.stderr
            if "見つかりません" not in combined and "cannot find" not in combined:
                raise RuntimeError(combined)