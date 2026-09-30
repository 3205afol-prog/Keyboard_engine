import sys
import subprocess
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QMessageBox,
    QSystemTrayIcon, QMenu
)

from pages.home_page import HomePage
from pages.layout_page import LayoutPage
from pages.settings_page import SettingsPage
from pages.about_page import AboutPage
from core.config_manager import load_config

from datetime import datetime

LOG_FILE = Path(__file__).resolve().parent / "debug_log.txt"
LOG_MAX_LINES = 500


def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} [launcher] {msg}\n")

    try:
        lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
        if len(lines) > LOG_MAX_LINES:
            LOG_FILE.write_text(
                "\n".join(lines[-LOG_MAX_LINES:]) + "\n", encoding="utf-8"
            )
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
ENGINE_SCRIPT = BASE_DIR / "engine.py"


class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KeyboardEngine ランチャー")
        self.resize(700, 450)

        self.engine_process = None
        self.tray_icon = None
        self.tray_enabled = False

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(150)
        for name in ["ホーム", "レイアウト", "設定", "情報"]:
            QListWidgetItem(name, self.sidebar)
        self.sidebar.currentRowChanged.connect(self.change_page)

        self.pages = QStackedWidget()
        self.pages.addWidget(HomePage(self))
        self.pages.addWidget(LayoutPage(self))
        self.pages.addWidget(SettingsPage(self))
        self.pages.addWidget(AboutPage(self))

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(self.pages)

        self.sidebar.setCurrentRow(0)

    def change_page(self, index: int):
        self.pages.setCurrentIndex(index)

    def start_engine(self):
        if self.is_engine_running():
            QMessageBox.information(self, "情報", "すでに起動しています")
            return None
        if not ENGINE_SCRIPT.exists():
            QMessageBox.critical(self, "エラー", f"engine.py が見つかりません:\n{ENGINE_SCRIPT}")
            return None
        try:
            self.engine_process = subprocess.Popen(
                [sys.executable, str(ENGINE_SCRIPT)], cwd=str(BASE_DIR)
            )
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"起動に失敗しました:\n{e}")
            return None
        return self.engine_process

    def stop_engine(self):
        if self.is_engine_running():
            self.engine_process.terminate()
        self.engine_process = None

    def is_engine_running(self) -> bool:
        return self.engine_process is not None and self.engine_process.poll() is None

    def setup_tray_icon(self):
        self.tray_enabled = True
        icon = self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
        self.tray_icon = QSystemTrayIcon(icon, self)

        menu = QMenu()
        show_action = menu.addAction("表示")
        show_action.triggered.connect(self.show_from_tray)
        quit_action = menu.addAction("終了")
        quit_action.triggered.connect(self.quit_app)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_from_tray()

    def show_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def quit_app(self):
        self.stop_engine()
        if self.tray_icon:
            self.tray_icon.hide()
        QApplication.instance().quit()

    def closeEvent(self, event):
        if self.tray_enabled:
            event.ignore()
            self.hide()
        else:
            self.stop_engine()
            event.accept()

def main(start_minimized: bool = False, autostart_engine: bool = False):
    log(f"launcher.main 開始 start_minimized={start_minimized} autostart_engine={autostart_engine}")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    config = load_config()
    window = LauncherWindow()

    if config["startup"]["minimize_to_tray"]:
        window.setup_tray_icon()

    should_minimize = start_minimized or config["startup"]["start_minimized"]

    if should_minimize and config["startup"]["minimize_to_tray"]:
        window.hide()
    elif should_minimize:
        window.showMinimized()
    else:
        window.show()
        window.raise_()
        window.activateWindow()

    # ← インデントを戻し、if/elif/elseの外に出す
    if autostart_engine:
        log("autostart_engine=True → start_engine呼び出し")
        window.start_engine()
        home_page = window.pages.widget(0)
        if hasattr(home_page, "sync_status_from_launcher"):
            home_page.sync_status_from_launcher()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()