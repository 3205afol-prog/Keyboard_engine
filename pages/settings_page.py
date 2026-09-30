import platform

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout,
    QCheckBox, QComboBox, QPushButton, QMessageBox, QLabel
)

from core.config_manager import load_config, save_config

TOGGLE_KEY_OPTIONS = [
    ("CapsLock", "capslock"),
    ("左Ctrl", "ctrl"),
    ("左Alt", "alt"),
    ("左Win / Command", "win_or_cmd"),
    ("左Shift", "shift"),
]


class SettingsPage(QWidget):
    def __init__(self, launcher_window):
        super().__init__()
        self.launcher_window = launcher_window
        self.config = load_config()
        self.is_mac = platform.system() == "Darwin"

        layout = QVBoxLayout(self)

        layout.addWidget(self._build_startup_group())
        layout.addWidget(self._build_toggle_key_group())
        layout.addWidget(self._build_block_group())
        layout.addStretch()

        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_button)

    def _build_startup_group(self):
        group = QGroupBox("起動・常駐設定")
        v = QVBoxLayout(group)

        self.run_on_boot_cb = QCheckBox("Windows起動時にKeyboard Engineを起動")
        self.start_minimized_cb = QCheckBox("最小化して起動")
        self.minimize_to_tray_cb = QCheckBox("タスクトレイに常駐")

        self.run_on_boot_cb.setChecked(self.config["startup"]["run_on_boot"])
        self.start_minimized_cb.setChecked(self.config["startup"]["start_minimized"])
        self.minimize_to_tray_cb.setChecked(self.config["startup"]["minimize_to_tray"])

        if self.is_mac:
            self.run_on_boot_cb.setEnabled(False)
            self.run_on_boot_cb.setToolTip("Macは現在未対応です")

        v.addWidget(self.run_on_boot_cb)
        v.addWidget(self.start_minimized_cb)
        v.addWidget(self.minimize_to_tray_cb)
        return group

    def _build_toggle_key_group(self):
        group = QGroupBox("エンジン切替キー")
        form = QFormLayout(group)

        self.toggle_key_combo = QComboBox()
        for label, value in TOGGLE_KEY_OPTIONS:
            self.toggle_key_combo.addItem(label, value)

        current = self.config.get("toggle_key", "capslock")
        index = next((i for i, (_, v) in enumerate(TOGGLE_KEY_OPTIONS) if v == current), 0)
        self.toggle_key_combo.setCurrentIndex(index)

        form.addRow("切替キー:", self.toggle_key_combo)

        note = QLabel(
            "※ CapsLock以外を選ぶと、そのキーは常にエンジンに横取りされ\n"
            "OS本来の機能（Ctrl+C, Alt+Tab等）が使えなくなります。"
        )
        note.setStyleSheet("color: gray; font-size: 11px;")
        form.addRow(note)
        return group

    def _build_block_group(self):
        meta_label = "Command + キー" if self.is_mac else "Win + キー"
        alt_label = "Option + キー" if self.is_mac else "Alt + キー"

        group = QGroupBox("以下の組み合わせでは変換しない")
        v = QVBoxLayout(group)

        self.block_ctrl_cb = QCheckBox("Ctrl + キー")
        self.block_alt_cb = QCheckBox(alt_label)
        self.block_meta_cb = QCheckBox(meta_label)

        bm = self.config.get("block_modifiers", {})
        self.block_ctrl_cb.setChecked(bm.get("ctrl", True))
        self.block_alt_cb.setChecked(bm.get("alt", True))
        self.block_meta_cb.setChecked(bm.get("meta", True))

        v.addWidget(self.block_ctrl_cb)
        v.addWidget(self.block_alt_cb)
        v.addWidget(self.block_meta_cb)
        return group

    def save_settings(self):
        self.config["startup"]["run_on_boot"] = self.run_on_boot_cb.isChecked()
        self.config["startup"]["start_minimized"] = self.start_minimized_cb.isChecked()
        self.config["startup"]["minimize_to_tray"] = self.minimize_to_tray_cb.isChecked()
        self.config["toggle_key"] = self.toggle_key_combo.currentData()
        self.config["block_modifiers"] = {
            "ctrl": self.block_ctrl_cb.isChecked(),
            "alt": self.block_alt_cb.isChecked(),
            "meta": self.block_meta_cb.isChecked(),
        }

        save_config(self.config)

        if platform.system() == "Windows":
            try:
                from core.startup_manager import set_startup_enabled
                set_startup_enabled(self.run_on_boot_cb.isChecked())
            except Exception as e:
                QMessageBox.warning(self, "警告", f"スタートアップ登録に失敗しました:\n{e}")

        QMessageBox.information(
            self, "保存しました",
            "設定を保存しました。\nエンジン起動中の場合、変更を反映するには一度停止して再起動してください。"
        )