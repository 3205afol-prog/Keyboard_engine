import Quartz
import os

KEYCODE_TABLE = {
    0:"a", 1:"s", 2:"d", 3:"f", 4:"h", 5:"g", 6:"z", 7:"x", 8:"c", 9:"v",
    11:"b", 12:"q", 13:"w", 14:"e", 15:"r", 16:"y", 17:"t",
    31:"o", 32:"u", 34:"i", 35:"p", 37:"l", 38:"j", 40:"k", 45:"n", 46:"m",
    41:";", 43:",", 47:".", 44:"/", 27:"-"
}
CHAR_TABLE = {v: k for k, v in KEYCODE_TABLE.items()}

TOGGLE_KEYCODE = {
    "capslock": 57,
    "ctrl": 59,
    "alt": 58,
    "win_or_cmd": 55,
    "shift": 56,
}

TOGGLE_FLAG_MASK = {
    "capslock": Quartz.kCGEventFlagMaskAlphaShift,
    "ctrl": Quartz.kCGEventFlagMaskControl,
    "alt": Quartz.kCGEventFlagMaskAlternate,
    "win_or_cmd": Quartz.kCGEventFlagMaskCommand,
    "shift": Quartz.kCGEventFlagMaskShift,
}


def keycode_to_char(keycode):
    return KEYCODE_TABLE.get(keycode)


def char_to_keycode(char):
    return CHAR_TABLE.get(char)


def run(remapper, config):

    toggle_key_name = config.get("toggle_key", "ctrl")
    toggle_keycode = TOGGLE_KEYCODE.get(toggle_key_name, 59)
    toggle_flag = TOGGLE_FLAG_MASK.get(toggle_key_name, Quartz.kCGEventFlagMaskControl)

    block = config.get("block_modifiers", {})
    block_ctrl = block.get("ctrl", True)
    block_alt = block.get("alt", True)
    block_meta = block.get("meta", True)  # Command

    engine_enabled = True
    toggle_pressed = False
    toggle_used_with_other = False

    def callback(proxy, event_type, event, refcon):

        nonlocal toggle_pressed, toggle_used_with_other, engine_enabled

        keycode = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)

        if keycode == toggle_keycode and event_type == Quartz.kCGEventFlagsChanged:

            flags = Quartz.CGEventGetFlags(event)
            toggle_now = bool(flags & toggle_flag)

            if toggle_now and not toggle_pressed:
                toggle_pressed = True
                toggle_used_with_other = False

            if toggle_pressed and keycode != toggle_keycode:
                toggle_used_with_other = True

            elif not toggle_now and toggle_pressed:
                if not toggle_used_with_other:
                    engine_enabled = not engine_enabled
                    if engine_enabled:
                        print("Keyboard engine running (mac)")
                        os.system("afplay /System/Library/Sounds/Ping.aiff &")
                    else:
                        print("Keyboard engine stopping (mac)")
                        os.system("afplay /System/Library/Sounds/Funk.aiff &")
                toggle_pressed = False

            return event

        if not engine_enabled:
            return event

        if event_type != Quartz.kCGEventKeyDown:
            return event

        flags = Quartz.CGEventGetFlags(event)

        block_flags = 0
        if block_ctrl:
            block_flags |= Quartz.kCGEventFlagMaskControl
        if block_alt:
            block_flags |= Quartz.kCGEventFlagMaskAlternate
        if block_meta:
            block_flags |= Quartz.kCGEventFlagMaskCommand

        if flags & block_flags:
            return event

        char = keycode_to_char(keycode)
        if char is None:
            return event

        new_char = remapper.transform(char)
        if new_char == char:
            return event

        new_keycode = char_to_keycode(new_char)
        if new_keycode is None:
            return event

        Quartz.CGEventSetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode, new_keycode)
        return event

    event_mask = (
        Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown) |
        Quartz.CGEventMaskBit(Quartz.kCGEventKeyUp) |
        Quartz.CGEventMaskBit(Quartz.kCGEventFlagsChanged)
    )

    tap = Quartz.CGEventTapCreate(
        Quartz.kCGSessionEventTap,
        Quartz.kCGHeadInsertEventTap,
        0,
        event_mask,
        callback,
        None
    )

    run_loop_source = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
    Quartz.CFRunLoopAddSource(Quartz.CFRunLoopGetCurrent(), run_loop_source, Quartz.kCFRunLoopCommonModes)
    Quartz.CGEventTapEnable(tap, True)

    print("Keyboard engine running (mac)")
    Quartz.CFRunLoopRun()