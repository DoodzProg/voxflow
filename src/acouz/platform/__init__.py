"""
AcouZ - Open-source AI voice dictation
Copyright (c) 2025-2026 DoodzProg
Licensed under the MIT License

src/acouz/platform/__init__.py

Platform abstraction layer.  Import OS-specific functions from here; the
correct backend (windows or linux) is selected automatically at import time.

Public API
----------
apply_dwm_rounded_corners(hwnd)   -- rounded corners on Win11, no-op elsewhere
set_app_user_model_id()           -- taskbar identity on Windows, no-op elsewhere
get_foreground_window()           -- active window handle (HWND / XID)
capture_selected_text(clipboard)  -- grab selected text from foreground app
is_startup_enabled()              -- check autostart registration
set_startup(enabled)              -- add / remove autostart entry
start_window_drag(hwnd)           -- native frameless-window drag
read_hotkey()                     -- blocking hotkey capture for rebinding UI
is_key_pressed(key)               -- check if a key is currently held down
send_paste()                      -- inject Ctrl+V into the focused window
"""

import sys

if sys.platform == "win32":
    from .windows import (  # noqa: F401
        apply_dwm_rounded_corners,
        set_app_user_model_id,
        get_foreground_window,
        capture_selected_text,
        is_startup_enabled,
        set_startup,
        start_window_drag,
        read_hotkey,
        is_key_pressed,
        send_paste,
    )
else:
    from .linux import (  # noqa: F401
        apply_dwm_rounded_corners,
        set_app_user_model_id,
        get_foreground_window,
        capture_selected_text,
        is_startup_enabled,
        set_startup,
        start_window_drag,
        read_hotkey,
        is_key_pressed,
        send_paste,
    )
