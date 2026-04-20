"""
AcouZ - Open-source AI voice dictation
Copyright (c) 2025-2026 DoodzProg
Licensed under the MIT License

src/acouz/platform/linux.py

Linux implementations of the platform abstraction layer.

Phase 2 functions (implemented here):
  - is_key_pressed()         pynput global listener — no root required
  - read_hotkey()            pynput blocking combo capture
  - get_foreground_window()  xdotool getactivewindow
  - capture_selected_text()  xdotool Ctrl+C + xclip
  - send_paste()             xdotool Ctrl+V
  - start_window_drag()      no-op — TitleBar handles Qt mouse drag on Linux
  - apply_dwm_rounded_corners() no-op — AcouZApp applies setMask() on Linux

Phase 3 stubs (not yet implemented):
  - is_startup_enabled() / set_startup()  ~/.config/autostart/acouz.desktop
"""

from __future__ import annotations

import subprocess
import threading
import time
from typing import Optional, Set


# ---------------------------------------------------------------------------
# pynput key-name normalisation
# ---------------------------------------------------------------------------

#: Maps pynput Key.name strings to keyboard-library-compatible key names.
_PYNPUT_TO_STD: dict[str, str] = {
    "ctrl_l":    "ctrl",    "ctrl_r":    "ctrl",
    "shift_l":   "shift",   "shift_r":   "shift",
    "alt_l":     "alt",     "alt_r":     "alt",
    "alt_gr":    "alt",
    "super_l":   "windows", "super_r":   "windows",
    "caps_lock": "caps lock",
    "num_lock":  "num lock",
    "scroll_lock": "scroll lock",
    "page_up":   "page up", "page_down": "page down",
    "print_screen": "print screen",
}


def _normalise_pynput_key(key) -> str:
    """Convert a pynput ``Key`` or ``KeyCode`` to a keyboard-library string.

    Args:
        key: A pynput ``keyboard.Key`` special key or ``keyboard.KeyCode`` char.

    Returns:
        Lowercase string compatible with keyboard-library naming conventions.
    """
    try:
        ch = key.char
        if ch:
            return ch.lower()
    except AttributeError:
        pass
    name = getattr(key, "name", str(key)).lower()
    return _PYNPUT_TO_STD.get(name, name)


# ---------------------------------------------------------------------------
# Global pynput key-state listener
# ---------------------------------------------------------------------------

_pressed_keys: Set[str] = set()
_pressed_lock = threading.Lock()
_global_listener: Optional[object] = None
_listener_start_lock = threading.Lock()


def _ensure_global_listener() -> None:
    """Start the module-level pynput listener if it is not already running.

    The listener is a daemon thread so it does not prevent application exit.
    Safe to call from any thread; protected by ``_listener_start_lock``.
    """
    global _global_listener
    with _listener_start_lock:
        alive = (
            _global_listener is not None
            and getattr(_global_listener, "is_alive", lambda: False)()
        )
        if alive:
            return
        try:
            from pynput import keyboard as _kb  # noqa: PLC0415

            def _on_press(key: object) -> None:
                with _pressed_lock:
                    _pressed_keys.add(_normalise_pynput_key(key))

            def _on_release(key: object) -> None:
                with _pressed_lock:
                    _pressed_keys.discard(_normalise_pynput_key(key))

            listener = _kb.Listener(
                on_press=_on_press,
                on_release=_on_release,
                daemon=True,
            )
            listener.start()
            _global_listener = listener
        except Exception as exc:
            print(f"[platform.linux] pynput listener start failed: {exc}")


# ---------------------------------------------------------------------------
# Window chrome
# ---------------------------------------------------------------------------

def apply_dwm_rounded_corners(hwnd: int) -> None:
    """No-op — rounded corners are applied via Qt ``setMask`` inside ``AcouZApp``."""
    pass


def set_app_user_model_id() -> None:
    """No-op on Linux — taskbar identity managed by the ``.desktop`` file."""
    pass


def start_window_drag(hwnd: int) -> None:
    """No-op — frameless-window drag is handled by Qt mouse events in ``TitleBar``."""
    pass


# ---------------------------------------------------------------------------
# Foreground window
# ---------------------------------------------------------------------------

def get_foreground_window() -> int:
    """Return the XID of the currently focused X11 window via ``xdotool``.

    Returns:
        Integer X11 window ID, or 0 if ``xdotool`` is unavailable or the
        call fails.
    """
    try:
        result = subprocess.run(
            ["xdotool", "getactivewindow"],
            capture_output=True,
            text=True,
            timeout=1.0,
        )
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError, OSError):
        pass
    return 0


# ---------------------------------------------------------------------------
# Selected-text capture
# ---------------------------------------------------------------------------

def capture_selected_text(clipboard) -> str:  # noqa: ANN001
    """Copy the foreground selection to the clipboard via ``xdotool``, then
    read it back with ``xclip``.

    Sends ``Ctrl+C`` with ``--clearmodifiers`` so that any held modifier keys
    (e.g. the hotkey itself) do not interfere with the copy action.

    Args:
        clipboard: Unused on Linux (kept for API parity with ``windows.py``).

    Returns:
        The selected text string, or ``""`` on any failure.
    """
    try:
        subprocess.run(
            ["xdotool", "key", "--clearmodifiers", "ctrl+c"],
            check=False,
            timeout=2.0,
        )
        # Give the target application time to update the clipboard.
        time.sleep(0.15)

        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True,
            text=True,
            timeout=2.0,
        )
        if result.returncode == 0:
            return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return ""


# ---------------------------------------------------------------------------
# Autostart — ~/.config/autostart  (Phase 3 stubs)
# ---------------------------------------------------------------------------

def is_startup_enabled() -> bool:
    """Check for ``~/.config/autostart/acouz.desktop`` — stub returns ``False``.

    Returns:
        Always ``False`` until Phase 3 implementation.
    """
    # TODO Phase 3: check ~/.config/autostart/acouz.desktop exists
    return False


def set_startup(enabled: bool) -> None:
    """Write / remove ``~/.config/autostart/acouz.desktop`` — stub no-op.

    Args:
        enabled: Unused until Phase 3.
    """
    # TODO Phase 3: create/delete ~/.config/autostart/acouz.desktop
    pass


# ---------------------------------------------------------------------------
# Hotkey recording
# ---------------------------------------------------------------------------

def read_hotkey() -> str:
    """Block until the user presses and starts releasing a key combination.

    Uses pynput so that no root privileges are required.  The combo is captured
    on the first key-release event after at least one key has been pressed.

    Returns:
        Hotkey string in keyboard-library format, e.g. ``"ctrl+shift"``.
        Keys are sorted alphabetically before joining.  Returns ``""`` on
        timeout (30 s) or any error.
    """
    try:
        from pynput import keyboard as _kb  # noqa: PLC0415

        _held: set[str] = set()
        _result: list[str] = []
        _done = threading.Event()

        def _on_press(key: object) -> None:
            _held.add(_normalise_pynput_key(key))

        def _on_release(key: object) -> None:
            if _held and not _result:
                _result.append("+".join(sorted(_held)))
                _done.set()
            return False  # Stop the listener immediately after first release.

        with _kb.Listener(on_press=_on_press, on_release=_on_release):
            _done.wait(timeout=30.0)

        return _result[0] if _result else ""
    except Exception as exc:
        print(f"[platform.linux] read_hotkey error: {exc}")
        return ""


# ---------------------------------------------------------------------------
# Key-state query
# ---------------------------------------------------------------------------

def is_key_pressed(key: str) -> bool:
    """Check whether *key* is currently held down.

    Backed by the global pynput listener started on first call.  Does **not**
    require root privileges.

    Args:
        key: Normalised key name (already stripped of ``"right "`` / ``"left "``
             prefix by :meth:`~acouz.core.hotkey.HotkeyListener._parse_keys`),
             e.g. ``"ctrl"``, ``"shift"``, ``"alt"``.

    Returns:
        ``True`` if the key is in the current pressed-keys set.
    """
    _ensure_global_listener()
    with _pressed_lock:
        return key.lower() in _pressed_keys


# ---------------------------------------------------------------------------
# Text injection
# ---------------------------------------------------------------------------

def send_paste() -> None:
    """Send ``Ctrl+V`` to the focused X11 window via ``xdotool``.

    ``--clearmodifiers`` ensures no stale modifier state from previous
    hotkey presses interferes with the paste action.
    """
    try:
        subprocess.run(
            ["xdotool", "key", "--clearmodifiers", "ctrl+v"],
            check=False,
            timeout=2.0,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
