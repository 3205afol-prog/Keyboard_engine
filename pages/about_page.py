import subprocess
import webbrowser
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt

APP_VERSION = "0.1.0"
APP_AUTHOR = "unkn-own"
GITHUB_URL = "https://github.com/3205afol-prog/Keyboard_engine"

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = BASE_DIR / "debug_log.txt"


class AboutPage(QWidget):
    def __init__(self, launcher_window):
        super().__init__()
        self.launcher_window = launcher_window

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        title = QLabel("KeyboardEngine")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")

        version_label = QLabel(f"バージョン: {APP_VERSION}")
        version_label.setAlignment(Qt.AlignCenter)

        author_label = QLabel(f"作者: {APP_AUTHOR}")
        author_label.setAlignment(Qt.AlignCenter)

        github_button = QPushButton("GitHub リポジトリを開く")
        github_button.clicked.connect(self.open_github)

        log_button = QPushButton("ログファイルを開く")
        log_button.clicked.connect(self.open_log_file)

        layout.addWidget(title)
        layout.addWidget(version_label)
        layout.addWidget(author_label)
        layout.addWidget(github_button)
        layout.addWidget(log_button)

    def open_github(self):
        webbrowser.open(GITHUB_URL)

    def open_log_file(self):
        if not LOG_FILE.exists():
            QMessageBox.information(self, "情報", "ログファイルがまだ存在しません")
            return
        try:
            subprocess.Popen(["notepad.exe", str(LOG_FILE)])
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ログファイルを開けませんでした:\n{e}")