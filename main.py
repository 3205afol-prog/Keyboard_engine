import ctypes
import platform
import sys
import traceback
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
MUTEX_NAME = "Global\\KeyboardEngineLauncher_Mutex"
ERROR_ALREADY_EXISTS = 183

LOG_FILE = BASE_DIR / "debug_log.txt"
LOG_MAX_LINES = 500  # これを超えたら古い行から削る


def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} {msg}\n")

    # 肥大化防止：直近 LOG_MAX_LINES 行だけ残す
    try:
        lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
        if len(lines) > LOG_MAX_LINES:
            LOG_FILE.write_text(
                "\n".join(lines[-LOG_MAX_LINES:]) + "\n", encoding="utf-8"
            )
    except Exception:
        pass


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin():
    params = " ".join(f'"{arg}"' for arg in sys.argv)
    result = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, str(BASE_DIR), 1
    )
    if result <= 32:
        log(f"昇格起動に失敗しました。エラーコード: {result}")


def acquire_single_instance_lock():
    if platform.system() == "Windows":
        handle = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
        last_error = ctypes.windll.kernel32.GetLastError()
        if last_error == ERROR_ALREADY_EXISTS:
            return None
        return handle
    else:
        import fcntl
        lock_path = BASE_DIR / ".launcher.lock"
        lock_file = open(lock_path, "w")
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return None
        return lock_file


def main():
    log(f"===== main.py 起動 argv={sys.argv}")
    system = platform.system()

    is_admin_result = is_admin()
    log(f"is_admin() = {is_admin_result}")

    if system == "Windows" and not is_admin_result:
        log("管理者権限なし → 事前チェック")
        pre_lock = acquire_single_instance_lock()
        if pre_lock is None:
            log("事前チェックで既に起動中と判定 → 終了")
            ctypes.windll.user32.MessageBoxW(0, "既に起動しています。", "KeyboardEngine", 0x40)
            sys.exit(0)
        else:
            log("事前チェックOK、解放して昇格へ")
            ctypes.windll.kernel32.CloseHandle(pre_lock)

        log("relaunch_as_admin 呼び出し")
        relaunch_as_admin()
        log("relaunch_as_admin 完了、終了")
        sys.exit(0)

    log("管理者権限あり → 本チェック")
    lock = acquire_single_instance_lock()
    if lock is None:
        log("本チェックで既に起動中と判定 → 終了")
        if system == "Windows":
            ctypes.windll.user32.MessageBoxW(0, "既に起動しています。", "KeyboardEngine", 0x40)
        else:
            print("既に起動しています。")
        sys.exit(0)

    log("ロック取得成功、launcher起動へ")

    start_minimized = "--minimized" in sys.argv
    autostart = "--autostart" in sys.argv
    log(f"start_minimized={start_minimized} autostart={autostart}")

    from launcher import main as launcher_main
    launcher_main(start_minimized=start_minimized, autostart_engine=autostart)

    log("launcher_main 終了")
    _ = lock


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log("★★★ 例外発生 ★★★")
        log(traceback.format_exc())