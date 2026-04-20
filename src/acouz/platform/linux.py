"""
AcouZ - Open-source AI voice dictation
Copyright (c) 2025-2026 DoodzProg
Licensed under the MIT License

src/acouz/platform/linux.py

Linux stubs for the platform abstraction layer.
Full implementations will be added in Phase 2 (pynput, xdotool, xclip,
~/.config/autostart).  All functions here are intentionally no-ops or return
safe zero-value defaults so the application imports and runs on Linux today.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Window chrome
# ---------------------------------------------------------------------------

def apply_dwm_rounded_corners(hwnd: int) -> None:
    """No-op on Linux — window rounding is handled by the compositor."""
    pass


def set_app_user_model_id() -> None:
    """No-op on Linux — taskbar identity managed by the .desktop file."""
    pass


def start_window_drag(hwnd: int) -> None:
    """No-op on Linux — Qt handles frameless-window drag natively via _NET_WM."""
    pass


# ---------------------------------------------------------------------------
# Foreground window
# ---------------------------------------------------------------------------

def get_foreground_window() -> int:
    """Return 0 — active window detection via xdotool added in Phase 2.

    Returns:
        Always 0 (no window handle).
    """
    # TODO Phase 2: subprocess xdotool getactivewindow
    return 0


# ---------------------------------------------------------------------------
# Selected-text capture
# ---------------------------------------------------------------------------

def capture_selected_text(clipboard) -> str:  # noqa: ANN001
    """Return empty string — xdotool/xclip implementation added in Phase 2.

    Args:
        clipboard: Unused on Linux (kept for API parity with windows.py).

    Returns:
        Always "".
    """
    # TODO Phase 2: xdotool key ctrl+c + xclip read
    return ""


# ---------------------------------------------------------------------------
# Autostart — ~/.config/autostart
# ---------------------------------------------------------------------------

def is_startup_enabled() -> bool:
    """Check for ~/.config/autostart/acouz.desktop — stub returns False.

    Returns:
        Always False until Phase 3 implementation.
    """
    # TODO Phase 3: check ~/.config/autostart/acouz.desktop exists
    return False


def set_startup(enabled: bool) -> None:
    """Write / remove ~/.config/autostart/acouz.desktop — stub no-op.

    Args:
        enabled: Unused until Phase 3.
    """
    # TODO Phase 3: create/delete ~/.config/autostart/acouz.desktop
    pass


# ---------------------------------------------------------------------------
# Hotkey recording
# ---------------------------------------------------------------------------

def read_hotkey() -> str:
    """Return empty string — pynput implementation added in Phase 2.

    Returns:
        Always "".
    """
    # TODO Phase 2: pynput-based blocking hotkey capture
    return ""
