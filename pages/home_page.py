import subprocess
from pathlib import Path

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PySide6.QtCore import Qt

BASE_DIR = Path(__file__).resolve().parent.parent
INSTALLER_EXE = BASE_DIR / "installer" / "Installer.exe"


class HomePage(QWidget):
    def __init__(self, launcher_window):
        super().__init__()
        self.launcher_window = launcher_window

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.status_label = QLabel("待機中")
        self.status_label.setAlignment(Qt.AlignCenter)

        self.start_button = QPushButton("開始")
        self.start_button.setFixedHeight(50)
        self.start_button.clicked.connect(self.start_engine)

        self.stop_button = QPushButton("停止")
        self.stop_button.setFixedHeight(50)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_engine)

        self.installer_button = QPushButton("インストーラーを起動")
        self.installer_button.clicked.connect(self.launch_installer)

        layout.addWidget(self.status_label)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.installer_button)

    def start_engine(self):
        if self.launcher_window.start_engine() is not None:
            self.status_label.setText("実行中")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

    def stop_engine(self):
        self.launcher_window.stop_engine()
        self.status_label.setText("待機中")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def launch_installer(self):
        if not INSTALLER_EXE.exists():
            QMessageBox.warning(self, "警告", f"インストーラーが見つかりません:\n{INSTALLER_EXE}")
            return
        subprocess.Popen([str(INSTALLER_EXE)], cwd=str(INSTALLER_EXE.parent))

    def sync_status_from_launcher(self):
        """launcher側で既にengineが起動している場合、UIを同期する"""
        if self.launcher_window.is_engine_running():
            self.status_label.setText("実行中")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)