"""
AcouZ - Open-source AI voice dictation
Copyright (c) 2025-2026 DoodzProg
Licensed under the MIT License

src/acouz/platform/linux.py

Linux implementations of the platform abstraction layer.

Global hotkey strategy (in priority order)
-------------------------------------------
1. **evdev** (``python-evdev``, ``/dev/input/event*``) — reads raw kernel
   input events; works on both X11 and Wayland; requires the current user to
   be in the ``input`` group (one-time setup, see below).
2. **pynput / Xlib** — fallback; works on X11 / XWayland sessions only when
   the target application is an X11 or XWayland client.  Will NOT intercept
   events from native Wayland windows.

To enable evdev (recommended on Ubuntu 22.04+ / Wayland)::

    sudo usermod -a -G input $USER
    # Log out and back in, then relaunch AcouZ.

Text injection / clipboard
--------------------------
- ``send_paste(target_wid)`` — uses ``xdotool key --window <wid> ctrl+v`` so
  the paste lands in the correct window even if AcouZ has stolen focus.
- ``capture_selected_text()`` — ``xdotool key --clearmodifiers ctrl+c`` then
  ``xclip -selection clipboard -o``.

Phase 3 stubs (not yet implemented)
------------------------------------
- ``is_startup_enabled()`` / ``set_startup()`` — ``~/.config/autostart/``
"""

from __future__ import annotations

import os
import subprocess
import threading
import time
from typing import Optional, Set


# ---------------------------------------------------------------------------
# Runtime environment detection
# ---------------------------------------------------------------------------

#: True when running inside a Wayland compositor (even under XWayland).
_ON_WAYLAND: bool = bool(os.environ.get("WAYLAND_DISPLAY"))


# ---------------------------------------------------------------------------
# evdev key-code → keyboard-library name mapping
# ---------------------------------------------------------------------------

#: Explicit map for modifier and special keys.  Character keys are derived
#: automatically from the ``KEY_`` prefix by stripping it and lowercasing.
_EVDEV_TO_STD: dict[int, str] = {}

def _build_evdev_map() -> None:
    """Populate ``_EVDEV_TO_STD`` after evdev is confirmed importable."""
    try:
        from evdev import ecodes  # noqa: PLC0415
        _EVDEV_TO_STD.update({
            ecodes.KEY_LEFTCTRL:   "ctrl",    ecodes.KEY_RIGHTCTRL:  "ctrl",
            ecodes.KEY_LEFTSHIFT:  "shift",   ecodes.KEY_RIGHTSHIFT: "shift",
            ecodes.KEY_LEFTALT:    "alt",     ecodes.KEY_RIGHTALT:   "alt",
            ecodes.KEY_LEFTMETA:   "windows", ecodes.KEY_RIGHTMETA:  "windows",
            ecodes.KEY_CAPSLOCK:   "caps lock",
            ecodes.KEY_NUMLOCK:    "num lock",
            ecodes.KEY_SCROLLLOCK: "scroll lock",
            ecodes.KEY_PAGEUP:     "page up",
            ecodes.KEY_PAGEDOWN:   "page down",
            ecodes.KEY_SPACE:      "space",
            ecodes.KEY_ENTER:      "enter",
            ecodes.KEY_KP_ENTER:   "enter",
            ecodes.KEY_TAB:        "tab",
            ecodes.KEY_BACKSPACE:  "backspace",
            ecodes.KEY_ESC:        "esc",
            ecodes.KEY_DELETE:     "delete",
            ecodes.KEY_INSERT:     "insert",
            ecodes.KEY_HOME:       "home",
            ecodes.KEY_END:        "end",
            ecodes.KEY_UP:         "up",
            ecodes.KEY_DOWN:       "down",
            ecodes.KEY_LEFT:       "left",
            ecodes.KEY_RIGHT:      "right",
        })
    except Exception:
        pass


def _evdev_key_to_std(keycode: int) -> str:
    """Convert an evdev key code to a keyboard-library-compatible string.

    Args:
        keycode: Raw evdev ``EV_KEY`` code.

    Returns:
        Normalised lowercase key name, e.g. ``"ctrl"``, ``"shift"``, ``"a"``.
    """
    if keycode in _EVDEV_TO_STD:
        return _EVDEV_TO_STD[keycode]
    try:
        from evdev import ecodes  # noqa: PLC0415
        name = ecodes.KEY.get(keycode, "")
        if isinstance(name, list):
            name = name[0] if name else ""
        if isinstance(name, str) and name.startswith("KEY_"):
            return name[4:].lower()  # KEY_A → "a", KEY_F1 → "f1"
    except Exception:
        pass
    return f"key_{keycode}"


# ---------------------------------------------------------------------------
# Shared key-state store (used by both evdev and pynput backends)
# ---------------------------------------------------------------------------

_pressed_keys: Set[str] = set()
_pressed_lock = threading.Lock()

# Listener state
_listener_started: bool = False
_listener_start_lock = threading.Lock()
_use_evdev: bool = False  # Set to True when evdev backend is active


# ---------------------------------------------------------------------------
# evdev backend
# ---------------------------------------------------------------------------

def _find_keyboard_devices() -> list:
    """Return a list of accessible evdev keyboard ``InputDevice`` objects.

    Filters by capability: the device must have ``EV_KEY``, ``KEY_A`` and
    ``KEY_LEFTCTRL``.  Devices that raise ``PermissionError`` are skipped —
    the caller should inform the user to join the ``input`` group.

    Returns:
        List of ``evdev.InputDevice`` instances (may be empty).
    """
    try:
        import evdev  # noqa: PLC0415
        from evdev import ecodes  # noqa: PLC0415
        _build_evdev_map()
        keyboards = []
        for path in evdev.list_devices():
            try:
                dev = evdev.InputDevice(path)
                caps = dev.capabilities()
                if (
                    ecodes.EV_KEY in caps
                    and ecodes.KEY_A in caps[ecodes.EV_KEY]
                    and ecodes.KEY_LEFTCTRL in caps[ecodes.EV_KEY]
                ):
                    keyboards.append(dev)
            except (PermissionError, OSError):
                pass
        return keyboards
    except ImportError:
        return []


def _evdev_read_loop(dev) -> None:
    """Blocking read loop for a single evdev ``InputDevice``.

    Runs in a daemon thread.  Updates ``_pressed_keys`` on every key-down and
    key-up event.  Exits silently on any I/O error (e.g. device removed).

    Args:
        dev: ``evdev.InputDevice`` to monitor.
    """
    try:
        from evdev import categorize, ecodes  # noqa: PLC0415
        for event in dev.read_loop():
            if event.type != ecodes.EV_KEY:
                continue
            ke = categorize(event)
            name = _evdev_key_to_std(ke.scancode)
            if ke.keystate in (ke.key_down, ke.key_hold):
                with _pressed_lock:
                    _pressed_keys.add(name)
            elif ke.keystate == ke.key_up:
                with _pressed_lock:
                    _pressed_keys.discard(name)
    except (OSError, IOError, AttributeError):
        pass


# ---------------------------------------------------------------------------
# pynput key-name normalisation (fallback backend)
# ---------------------------------------------------------------------------

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
    """Convert a pynput ``Key`` / ``KeyCode`` to a keyboard-library string.

    Args:
        key: A pynput ``keyboard.Key`` or ``keyboard.KeyCode`` object.

    Returns:
        Normalised lowercase key name.
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
# Listener bootstrap — auto-selects evdev or pynput
# ---------------------------------------------------------------------------

def _ensure_global_listener() -> None:
    """Start the global key-state listener if not already running.

    Tries evdev first (Wayland-compatible, no root required with ``input``
    group).  Falls back to pynput/Xlib if evdev is unavailable or if no
    accessible keyboard devices are found.

    Safe to call from any thread; protected by ``_listener_start_lock``.
    Subsequent calls after the first are no-ops.
    """
    global _listener_started, _use_evdev
    with _listener_start_lock:
        if _listener_started:
            return

        # ── Try evdev ────────────────────────────────────────────────
        devices = _find_keyboard_devices()
        if devices:
            for dev in devices:
                t = threading.Thread(
                    target=_evdev_read_loop, args=(dev,), daemon=True
                )
                t.start()
            _use_evdev = True
            _listener_started = True
            return

        # ── Fall back to pynput/Xlib ─────────────────────────────────
        if not _ON_WAYLAND:
            # pynput only works globally on X11 sessions.
            # On Wayland it only intercepts events for the AcouZ window.
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
                _listener_started = True
                return
            except Exception as exc:
                print(f"[platform.linux] pynput listener failed: {exc}")
        else:
            print(
                "[platform.linux] WARNING: Running on Wayland with no accessible "
                "evdev devices.  Global hotkeys will not work.\n"
                "  Fix: sudo usermod -a -G input $USER  then log out and back in."
            )

        _listener_started = True  # Don't retry on every is_key_pressed call.


# ---------------------------------------------------------------------------
# Window chrome
# ---------------------------------------------------------------------------

def apply_dwm_rounded_corners(hwnd: int) -> None:
    """No-op — rounded corners are applied via Qt ``setMask`` inside ``AcouZApp``."""
    pass


def set_app_user_model_id() -> None:
    """No-op on Linux — taskbar identity is managed by the ``.desktop`` file."""
    pass


def start_window_drag(hwnd: int) -> None:
    """No-op — frameless-window drag is handled by Qt mouse events in ``TitleBar``."""
    pass


# ---------------------------------------------------------------------------
# Foreground window
# ---------------------------------------------------------------------------

def get_foreground_window() -> int:
    """Return the XID of the currently focused X11 / XWayland window.

    Uses ``xdotool getactivewindow``.  On fully native Wayland sessions where
    the focused window has no X11 counterpart this will return 0.

    Returns:
        Integer X11 window XID, or 0 on any failure.
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
    """Copy the foreground selection via xdotool, then read it with xclip.

    Sends ``Ctrl+C`` with ``--clearmodifiers`` so that any held modifier keys
    do not interfere with the copy action.  A 150 ms delay is added before
    reading the clipboard to allow the target application to respond.

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

    Uses pynput so that no root privileges are required.  This function is
    called from the Settings page while AcouZ has focus; it does not need to
    work globally.

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
            return False  # Stop the listener after the first release.

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

    Backed by the evdev global listener (preferred) or the pynput/Xlib
    listener (fallback).  Started automatically on first call.

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

def send_paste(target_wid: int = 0) -> None:
    """Inject ``Ctrl+V`` into the target window via ``xdotool``.

    Using ``--window <wid>`` ensures the paste reaches the correct application
    even when AcouZ's overlay has stolen focus (e.g. after clicking ✓).
    Falls back to a focus-independent keypress if no ``target_wid`` is given.

    Args:
        target_wid: X11 window XID of the target application.  ``0`` means
                    "send to the currently focused window".
    """
    try:
        if target_wid:
            # Focus the target window, then send paste.
            subprocess.run(
                ["xdotool", "windowfocus", "--sync", str(target_wid)],
                check=False,
                timeout=2.0,
            )
            time.sleep(0.05)
            subprocess.run(
                ["xdotool", "key", "--window", str(target_wid),
                 "--clearmodifiers", "ctrl+v"],
                check=False,
                timeout=2.0,
            )
        else:
            subprocess.run(
                ["xdotool", "key", "--clearmodifiers", "ctrl+v"],
                check=False,
                timeout=2.0,
            )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
