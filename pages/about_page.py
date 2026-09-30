# pages/about_page.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class AboutPage(QWidget):
    def __init__(self, launcher_window):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("KeyboardEngine\nバージョン: 0.1.0"))