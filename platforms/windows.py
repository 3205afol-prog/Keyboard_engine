import ctypes
import threading
from ctypes import wintypes

user32 = ctypes.windll.user32

# 記号キーは配列(JIS/US)によって出力文字が変わるため、実行時に動的検出する対象
SYMBOL_VKS = [0xBA, 0xBB, 0xBC, 0xBD, 0xBE, 0xBF]

# アルファベットは配列によらず共通
LETTER_VK_TO_CHAR = {vk: chr(vk + 32) for vk in range(0x41, 0x5B)}


def _detect_symbol_char(vk_code):
    """Shiftなし状態で、このVKコードが実際に出力する文字を取得する"""
    scan_code = user32.MapVirtualKeyW(vk_code, 0)
    keyboard_state = (ctypes.c_byte * 256)()
    buf = ctypes.create_unicode_buffer(4)
    result = user32.ToUnicode(vk_code, scan_code, keyboard_state, buf, 4, 0)
    if result > 0:
        return buf.value[0]
    return None


def build_char_tables():
    vk_to_char = dict(LETTER_VK_TO_CHAR)
    for vk in SYMBOL_VKS:
        char = _detect_symbol_char(vk)
        if char is not None:
            vk_to_char[vk] = char
    char_to_vk = {v: k for k, v in vk_to_char.items()}
    return vk_to_char, char_to_vk

# =========================
# 定数
# =========================

WM_KEYDOWN = 0x0100
WM_KEYUP   = 0x0101

VK_CAPITAL  = 0x14
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LMENU    = 0xA4
VK_RMENU    = 0xA5
VK_LWIN     = 0x5B
VK_RWIN     = 0x5C
VK_LSHIFT   = 0xA0

# 設定画面で選べる切替キーとVKコードの対応
TOGGLE_KEY_VK = {
    "capslock": VK_CAPITAL,
    "ctrl": VK_LCONTROL,
    "alt": VK_LMENU,
    "win_or_cmd": VK_LWIN,
    "shift": VK_LSHIFT,
}

WH_KEYBOARD_LL = 13

LLKHF_INJECTED = 0x10

KEYEVENTF_KEYUP = 0x0002

user32.CallNextHookEx.argtypes = [
    wintypes.HHOOK,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM
]

user32.CallNextHookEx.restype = wintypes.LPARAM

# =========================
# Hook用構造体
# =========================

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p)
    ]

# =========================
# キー送信
# =========================

def send_key(vk):

    def worker():

        user32.keybd_event(
            vk,
            0,
            0,
            0
        )

        user32.keybd_event(
            vk,
            0,
            KEYEVENTF_KEYUP,
            0
        )

    threading.Timer(
        0.01,
        worker
    ).start()

# =========================
# Hook
# =========================

HOOKPROC = ctypes.WINFUNCTYPE(
    ctypes.c_int,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM
)

# run関数

def run(remapper, config):

    global pointer

    VK_TO_CHAR, CHAR_TO_VK = build_char_tables()

    toggle_key_name = config.get("toggle_key", "capslock")
    toggle_vk = TOGGLE_KEY_VK.get(toggle_key_name, VK_CAPITAL)

    block = config.get("block_modifiers", {})
    block_ctrl = block.get("ctrl", True)
    block_alt = block.get("alt", True)
    block_meta = block.get("meta", True)  # Win

    engine_enabled = True
    toggle_pressed = False
    toggle_used = False

    def hook_proc(nCode, wParam, lParam):

        nonlocal engine_enabled
        nonlocal toggle_pressed
        nonlocal toggle_used

        # nCode が負ならそのまま次へ
        if nCode < 0:
            return user32.CallNextHookEx(
                None,
                nCode,
                wParam,
                lParam
            )

        if wParam not in (WM_KEYDOWN, WM_KEYUP):
            return user32.CallNextHookEx(
                None,
                nCode,
                wParam,
                lParam
            )

        # lParam を KBDLLHOOKSTRUCT にキャストして kb を定義
        kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents

        if wParam == WM_KEYDOWN and kb.vkCode == toggle_vk:
            toggle_pressed = True
            toggle_used = False
            return 1

        if (
            toggle_pressed
            and kb.vkCode != toggle_vk
            and wParam == WM_KEYDOWN
        ):
            toggle_used = True

        if (
            wParam == WM_KEYUP
            and kb.vkCode == toggle_vk
        ):
            if not toggle_used:
                engine_enabled = not engine_enabled
                print(
                    f"KeyboardEngine {'ON' if engine_enabled else 'OFF'}"
                )

            toggle_pressed = False
            return 1

        if wParam != WM_KEYDOWN:
            return user32.CallNextHookEx(
                None,
                nCode,
                wParam,
                lParam
            )

        if kb.flags & LLKHF_INJECTED:
            return user32.CallNextHookEx(
                None,
                nCode,
                wParam,
                lParam
            )

        if not engine_enabled:
            return user32.CallNextHookEx(
                None,
                nCode,
                wParam,
                lParam
            )

        ctrl_down = bool(
            user32.GetAsyncKeyState(VK_LCONTROL) & 0x8000
            or
            user32.GetAsyncKeyState(VK_RCONTROL) & 0x8000
        )

        alt_down = bool(
            user32.GetAsyncKeyState(VK_LMENU) & 0x8000
            or
            user32.GetAsyncKeyState(VK_RMENU) & 0x8000
        )

        win_down = bool(
            user32.GetAsyncKeyState(VK_LWIN) & 0x8000
            or
            user32.GetAsyncKeyState(VK_RWIN) & 0x8000
        )

        if (
            (block_ctrl and ctrl_down)
            or (block_alt and alt_down)
            or (block_meta and win_down)
        ):
            return user32.CallNextHookEx(
                None,
                nCode,
                wParam,
                lParam
            )

        char = VK_TO_CHAR.get(
            kb.vkCode
        )

        if char is None:
            return user32.CallNextHookEx(
                None,
                nCode,
                wParam,
                lParam
            )

        new_char = remapper.transform(
            char
        )

        if new_char == char:
            return user32.CallNextHookEx(
                None,
                nCode,
                wParam,
                lParam
            )

        new_vk = CHAR_TO_VK.get(
            new_char
        )

        if new_vk is None:
            return user32.CallNextHookEx(
                None,
                nCode,
                wParam,
                lParam
            )

        send_key(new_vk)

        return 1

    pointer = HOOKPROC(hook_proc)

    hook = user32.SetWindowsHookExW(
        WH_KEYBOARD_LL,
        pointer,
        None,
        0
    )

    if not hook:
        raise OSError("Hook failed")

    print("KeyboardEngine Running")

    msg = wintypes.MSG()

    while True:
        user32.GetMessageW(
            ctypes.byref(msg),
            0,
            0,
            0
        )

        user32.TranslateMessage(
            ctypes.byref(msg)
        )

        user32.DispatchMessageW(
            ctypes.byref(msg)
        )