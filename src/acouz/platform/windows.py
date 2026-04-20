"""
AcouZ - Open-source AI voice dictation
Copyright (c) 2025-2026 DoodzProg
Licensed under the MIT License

src/acouz/platform/windows.py

Windows-specific implementations of the platform abstraction layer.
All functions here use Win32 APIs via ctypes, winreg, uiautomation, or the
keyboard library.  This module is only imported on sys.platform == "win32".
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import sys
import time


# ---------------------------------------------------------------------------
# Window chrome
# ---------------------------------------------------------------------------

def apply_dwm_rounded_corners(hwnd: int) -> None:
    """Ask the Windows 11 DWM compositor to round the window corners.

    Uses DwmSetWindowAttribute with DWMWA_WINDOW_CORNER_PREFERENCE (33) set
    to DWMWCP_ROUND (2).  Silently ignored on Windows 10 and older builds.

    Args:
        hwnd: Native window handle (QWidget.winId() cast to int).
    """
    try:
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_ROUND = ctypes.c_int(2)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(DWMWCP_ROUND),
            ctypes.sizeof(DWMWCP_ROUND),
        )
    except Exception:
        pass


def set_app_user_model_id() -> None:
    """Register AcouZ as its own taskbar entity.

    Without this the process groups under the generic Python interpreter icon.
    Must be called before any QApplication window is created.
    """
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "DoodzProg.AcouZ.1.0"
        )
    except Exception:
        pass


def start_window_drag(hwnd: int) -> None:
    """Trigger native Win32 window drag for a frameless window.

    Sends WM_NCLBUTTONDOWN with HTCAPTION so the OS handles the drag loop,
    giving correct Aero-Snap behaviour.

    Args:
        hwnd: Native window handle of the top-level window.
    """
    try:
        ctypes.windll.user32.ReleaseCapture()
        ctypes.windll.user32.SendMessageW(hwnd, 0xA1, 2, 0)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Foreground window
# ---------------------------------------------------------------------------

def get_foreground_window() -> int:
    """Return the HWND of the currently active window.

    Returns:
        Integer window handle, or 0 if the call fails.
    """
    try:
        return ctypes.windll.user32.GetForegroundWindow()
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Selected-text capture
# ---------------------------------------------------------------------------

def capture_selected_text(clipboard) -> str:
    """Capture the currently selected text from the foreground application.

    Plan A: UIAutomation — works with Notepad, Word, native controls.
    Plan B: Raw SendInput Ctrl+C scancode — fallback for Chromium-based apps.

    The clipboard is used as a transport in Plan B; callers are responsible for
    backing up and restoring its contents around this call.

    Args:
        clipboard: QApplication.clipboard() instance.

    Returns:
        The selected text string, or "" if nothing could be captured.
    """
    import keyboard  # noqa: PLC0415

    context_text = ""

    # Plan A: UIAutomation (Notepad, Word, native Win32 controls)
    try:
        import uiautomation as auto  # noqa: PLC0415
        auto.SetGlobalSearchTimeout(0.1)
        control = auto.GetFocusedControl()
        if control:
            pattern = control.GetTextPattern()
            if pattern:
                selections = pattern.GetSelection()
                if selections and len(selections) > 0:
                    context_text = selections[0].GetText()
    except Exception:
        pass

    # Plan B: Chromium fallback — raw SendInput scancodes + clipboard read
    if not context_text:
        try:
            keyboard.block_key(";")
            keyboard.block_key(":")
        except Exception:
            pass
        clipboard.clear()
        try:
            INPUT_KEYBOARD = 1
            KEYEVENTF_SCANCODE = 0x0008
            KEYEVENTF_KEYUP = 0x0002

            class KEYBDINPUT(ctypes.Structure):  # noqa: N801
                _fields_ = [
                    ("wVk", ctypes.c_ushort),
                    ("wScan", ctypes.c_ushort),
                    ("dwFlags", ctypes.c_ulong),
                    ("time", ctypes.c_ulong),
                    ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
                ]

            class INPUT(ctypes.Structure):  # noqa: N801
                class _INPUT(ctypes.Union):
                    _fields_ = [("ki", KEYBDINPUT)]
                _anonymous_ = ("_input",)
                _fields_ = [
                    ("type", ctypes.c_ulong),
                    ("_input", _INPUT),
                ]

            def _send(scancode: int, release: bool = False) -> None:
                flags = KEYEVENTF_SCANCODE | (KEYEVENTF_KEYUP if release else 0)
                ii_ = INPUT._INPUT()
                ii_.ki = KEYBDINPUT(
                    0, scancode, flags, 0,
                    ctypes.pointer(ctypes.c_ulong(0)),
                )
                x = INPUT(INPUT_KEYBOARD, ii_)
                ctypes.windll.user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

            _send(0x1D)        # Ctrl down
            _send(0x2E)        # C down
            _send(0x2E, True)  # C up
            _send(0x1D, True)  # Ctrl up
            time.sleep(0.15)
            context_text = clipboard.text()
        finally:
            try:
                keyboard.unblock_key(";")
                keyboard.unblock_key(":")
            except Exception:
                pass

    return context_text


# ---------------------------------------------------------------------------
# Autostart — Windows Registry
# ---------------------------------------------------------------------------

_APP_NAME = "AcouZ"
_RUN_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"


def _startup_cmd() -> str:
    """Return the Run-key command string for the current execution context."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    return f'"{sys.executable}" -m acouz.ui.app'


def is_startup_enabled() -> bool:
    """Check whether AcouZ is registered in the Windows startup Run key.

    Returns:
        True if the registry value exists, False otherwise.
    """
    try:
        import winreg  # noqa: PLC0415
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _RUN_KEY,
        )
        winreg.QueryValueEx(key, _APP_NAME)
        winreg.CloseKey(key)
        return True
    except (FileNotFoundError, OSError):
        return False


def set_startup(enabled: bool) -> None:
    """Add or remove the AcouZ registry startup entry.

    Args:
        enabled: True to register, False to deregister.
    """
    import winreg  # noqa: PLC0415

    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        _RUN_KEY,
        0,
        winreg.KEY_SET_VALUE,
    )
    if enabled:
        winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, _startup_cmd())
    else:
        try:
            winreg.DeleteValue(key, _APP_NAME)
        except FileNotFoundError:
            pass
    winreg.CloseKey(key)


# ---------------------------------------------------------------------------
# Hotkey recording
# ---------------------------------------------------------------------------

def read_hotkey() -> str:
    """Block until the user presses a key combination and return it.

    Returns:
        Hotkey string in keyboard-library format, e.g. "ctrl+shift".
    """
    import keyboard  # noqa: PLC0415
    return keyboard.read_hotkey(suppress=False)


# ---------------------------------------------------------------------------
# Key-state query
# ---------------------------------------------------------------------------

def is_key_pressed(key: str) -> bool:
    """Check whether *key* is currently held down using the keyboard library.

    Args:
        key: Normalised key name (already stripped of ``"right "`` / ``"left "``
             prefix), e.g. ``"ctrl"``, ``"shift"``.

    Returns:
        ``True`` if the key is currently pressed, ``False`` on any error.
    """
    import keyboard  # noqa: PLC0415
    try:
        return bool(keyboard.is_pressed(key))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Text injection
# ---------------------------------------------------------------------------

def send_paste() -> None:
    """Send ``Ctrl+V`` via the keyboard library to paste clipboard contents."""
    import keyboard  # noqa: PLC0415
    try:
        keyboard.send("ctrl+v")
    except Exception:
        pass
