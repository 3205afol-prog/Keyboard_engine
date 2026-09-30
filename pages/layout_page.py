from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QScrollArea, QMessageBox, QInputDialog,
    QTabBar, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from core.layout_manager import (
    list_presets, load_preset, save_preset, delete_preset,
    generate_preset_id, apply_preset_as_active, find_active_preset_id,
    EDITABLE_KEYS,
)

# QWERTY配列（表示用の行構成）
KEYBOARD_ROWS = [
    list("qwertyuiop"),
    list("asdfghjkl") + [";"],
    list("zxcvbnm") + [",", ".", "/"],
]

# 変換元として編集可能なキー(a-z + 記号)。qwertyの物理キー名と一致。
EDITABLE_SOURCE_KEYS = set(EDITABLE_KEYS)


class KeyButton(QPushButton):
    def __init__(self, source_key: str, page):
        super().__init__()
        self.source_key = source_key
        self.page = page
        self.setFixedSize(52, 52)
        self.setCheckable(True)
        self.clicked.connect(self.on_click)
        self.update_label()

    def update_label(self):
        target = self.page.current_mapping.get(self.source_key, self.source_key)
        if target == self.source_key:
            self.setText(self.source_key)
        else:
            self.setText(f"{self.source_key}\n→{target}")

    def on_click(self):
        self.page.select_key(self.source_key)


class LayoutPage(QWidget):
    def __init__(self, launcher_window):
        super().__init__()
        self.launcher_window = launcher_window

        self.current_preset_id = None
        self.current_mapping = {}
        self.clipboard_mapping = None
        self.selected_key = None
        self.key_buttons = {}

        self.setFocusPolicy(Qt.StrongFocus)

        root = QVBoxLayout(self)

        # タブバー
        self.tab_bar = QTabBar()
        self.tab_bar.setExpanding(False)
        self.tab_bar.setStyleSheet("""
            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #b0b0b0;
                border-bottom: none;
                padding: 6px 14px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border: 2px solid #1976d2;
                border-bottom: none;
                font-weight: bold;
                padding: 5px 13px;
            }
            QTabBar::tab:hover:!selected {
                background: #ececec;
            }
        """)
        self.tab_bar.currentChanged.connect(self.on_tab_changed)
        self.tab_bar.setExpanding(False)
        self.tab_bar.currentChanged.connect(self.on_tab_changed)
        root.addWidget(self.tab_bar)

        # 新規タブボタン（タブバーの右に配置）
        tab_row = QHBoxLayout()
        tab_row.addStretch()
        self.new_tab_button = QPushButton("＋ 新規プリセット")
        self.new_tab_button.clicked.connect(self.create_new_preset)
        tab_row.addWidget(self.new_tab_button)
        root.addLayout(tab_row)

        # ツールバー
        toolbar = QHBoxLayout()
        self.copy_button = QPushButton("コピー")
        self.copy_button.clicked.connect(self.copy_layout)
        self.paste_button = QPushButton("貼り付け")
        self.paste_button.clicked.connect(self.paste_layout)
        self.rename_button = QPushButton("名前変更")
        self.rename_button.clicked.connect(self.rename_preset)
        self.delete_button = QPushButton("削除")
        self.delete_button.clicked.connect(self.delete_current_preset)
        self.save_button = QPushButton("保存してエンジンに適用")
        self.save_button.clicked.connect(self.save_and_apply)

        toolbar.addWidget(self.copy_button)
        toolbar.addWidget(self.paste_button)
        toolbar.addWidget(self.rename_button)
        toolbar.addWidget(self.delete_button)
        toolbar.addStretch()
        toolbar.addWidget(self.save_button)
        root.addLayout(toolbar)

        # 選択中キーの表示
        self.selected_label = QLabel("キーを選択してください")
        self.selected_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.selected_label)

        # キーボード配置エリア
        keyboard_area = QVBoxLayout()
        keyboard_area.setAlignment(Qt.AlignCenter)
        for row_index, row_keys in enumerate(KEYBOARD_ROWS):
            row_layout = QHBoxLayout()
            row_layout.setAlignment(Qt.AlignCenter)
            row_layout.addSpacing(row_index * 20)
            for key in row_keys:
                btn = KeyButton(key, self)
                self.key_buttons[key] = btn
                row_layout.addWidget(btn)
            keyboard_area.addLayout(row_layout)
        root.addLayout(keyboard_area)

        root.addStretch()

        self.reload_tabs()

    # ---------- タブ管理 ----------

    def reload_tabs(self, select_id: str | None = None):
        self.tab_bar.blockSignals(True)

        # clear()の代わりに、末尾から1つずつ削除する
        while self.tab_bar.count() > 0:
            self.tab_bar.removeTab(0)

        active_id = find_active_preset_id()
        presets = list_presets()

        target_index = 0
        for i, info in enumerate(presets):
            label = info["name"]
            if info["id"] == active_id:
                label = f"● {label}"
            self.tab_bar.addTab(label)
            self.tab_bar.setTabData(i, info["id"])

            if info["id"] == active_id:
                self.tab_bar.setTabTextColor(i, QColor("#2e7d32"))

            if select_id is not None and info["id"] == select_id:
                target_index = i
            elif select_id is None and info["id"] == active_id:
                target_index = i

        self.tab_bar.blockSignals(False)
        self.tab_bar.setCurrentIndex(target_index)
        self.on_tab_changed(target_index)

    def on_tab_changed(self, index: int):
        if index < 0:
            return
        preset_id = self.tab_bar.tabData(index)
        if preset_id is None:
            return

        self.current_preset_id = preset_id
        self.current_mapping = load_preset(preset_id)
        self.selected_key = None
        self.selected_label.setText("キーを選択してください")
        self.refresh_key_buttons()

        info = next((p for p in list_presets() if p["id"] == preset_id), None)
        is_builtin = info["is_builtin"] if info else False
        self.delete_button.setEnabled(not is_builtin)
        self.rename_button.setEnabled(not is_builtin)

    def create_new_preset(self):
        new_id = generate_preset_id()
        save_preset(new_id, {}, name="新規プリセット")
        self.reload_tabs(select_id=new_id)

    def rename_preset(self):
        if self.current_preset_id is None:
            return
        info = next((p for p in list_presets() if p["id"] == self.current_preset_id), None)
        current_name = info["name"] if info else ""

        name, ok = QInputDialog.getText(self, "名前変更", "プリセット名:", text=current_name)
        if ok and name.strip():
            save_preset(self.current_preset_id, self.current_mapping, name=name.strip())
            self.reload_tabs(select_id=self.current_preset_id)

    def delete_current_preset(self):
        if self.current_preset_id is None:
            return
        reply = QMessageBox.question(
            self, "確認", "このプリセットを削除しますか？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_preset(self.current_preset_id)
            self.reload_tabs()

    # ---------- キー編集 ----------

    def select_key(self, key: str):
        # 他のボタンの選択状態を解除
        for k, btn in self.key_buttons.items():
            btn.setChecked(k == key)

        self.selected_key = key
        self.selected_label.setText(f"選択中: 「{key}」→ 変換先の文字を入力してください")
        self.setFocus()

    def keyPressEvent(self, event):
        if self.selected_key is None:
            return super().keyPressEvent(event)

        text = event.text().lower()
        if text not in EDITABLE_SOURCE_KEYS:
            return  # 対象外のキーは無視

        self.apply_mapping(self.selected_key, text)

    def apply_mapping(self, source_key: str, target_key: str):
        # 重複チェック（他のキーが既に同じ変換先を使っていないか）
        duplicates = [
            k for k, v in self.current_mapping.items()
            if v == target_key and k != source_key
        ]
        if duplicates:
            QMessageBox.warning(
                self, "警告",
                f"「{target_key}」は既に「{', '.join(duplicates)}」の変換先として使われています。\n"
                "このまま設定すると、複数のキーが同じ文字を出力します。"
            )

        if target_key == source_key:
            self.current_mapping.pop(source_key, None)
        else:
            self.current_mapping[source_key] = target_key

        self.refresh_key_buttons()
        self.selected_label.setText(f"「{source_key}」→「{target_key}」に設定しました")

    def refresh_key_buttons(self):
        for btn in self.key_buttons.values():
            btn.update_label()
            btn.setChecked(btn.source_key == self.selected_key)

    # ---------- コピー・貼り付け・保存 ----------

    def copy_layout(self):
        self.clipboard_mapping = dict(self.current_mapping)
        QMessageBox.information(self, "コピー", "現在のレイアウトをコピーしました")

    def paste_layout(self):
        if self.clipboard_mapping is None:
            QMessageBox.information(self, "情報", "コピーされたレイアウトがありません")
            return
        self.current_mapping = dict(self.clipboard_mapping)
        self.refresh_key_buttons()

    def save_and_apply(self):
        # 現在のタブ内容をプリセットとして保存
        info = next((p for p in list_presets() if p["id"] == self.current_preset_id), None)
        name = info["name"] if info else None
        save_preset(self.current_preset_id, self.current_mapping, name=name)

        # 実行中レイアウトとして適用
        apply_preset_as_active(self.current_mapping)

        # エンジンが動いていれば再起動して反映
        if self.launcher_window.is_engine_running():
            self.launcher_window.stop_engine()
            self.launcher_window.start_engine()

        self.reload_tabs(select_id=self.current_preset_id)
        QMessageBox.information(self, "保存完了", "レイアウトを保存し、エンジンに適用しました")