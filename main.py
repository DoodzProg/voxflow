"""
AcouZ - Open-source AI voice dictation
Copyright (c) 2025-2026 DoodzProg
Licensed under the MIT License

Application entry point used by both the development runner and PyInstaller.
All heavy imports happen inside the function so that the frozen exe starts
quickly and error messages are not lost before the event loop begins.
"""

import sys
import os


def _apply_dwm_rounded_corners(hwnd: int) -> None:
    """Ask the Windows 11 DWM compositor to round the window corners.

    Uses ``DwmSetWindowAttribute`` with ``DWMWA_WINDOW_CORNER_PREFERENCE``
    (attribute 33) set to ``DWMWCP_ROUND`` (value 2).

    This is a no-op on Windows 10 and non-Windows platforms — the call fails
    silently so the app still works everywhere.

    Args:
        hwnd: Native window handle returned by ``QWidget.winId()``.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes        # noqa: PLC0415
        import ctypes.wintypes  # noqa: PLC0415

        # DWMWA_WINDOW_CORNER_PREFERENCE = 33
        # DWMWCP_ROUND                   = 2
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_ROUND = ctypes.c_int(2)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(DWMWCP_ROUND),
            ctypes.sizeof(DWMWCP_ROUND),
        )
    except Exception:
        pass  # Non-fatal — Windows 10 / older builds simply ignore this.


def _set_app_user_model_id() -> None:
    """Tell Windows to treat AcouZ as its own taskbar entity.

    Without this call Windows groups the process under the generic Python
    interpreter icon.  Must be called before any window or QApplication is
    created so the Shell picks up the ID from the very first message pump.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes  # noqa: PLC0415
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "DoodzProg.AcouZ.1.0"
        )
    except Exception:
        pass  # Non-fatal — the app still works, just with the Python icon.


def main() -> None:
    """Bootstrap the AcouZ PySide6 application."""
    # Register AcouZ's own taskbar identity before anything else.
    _set_app_user_model_id()

    # When running from a PyInstaller bundle (_MEIPASS is set), the bundled
    # packages are already on sys.path.  In development we add src/ manually.
    if not getattr(sys, "frozen", False):
        src_dir = os.path.join(os.path.dirname(__file__), "src")
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)

    from acouz.utils.config import ConfigManager  # noqa: PLC0415
    from acouz.ui.app import AcouZApp             # noqa: PLC0415
    from PySide6.QtWidgets import QApplication     # noqa: PLC0415

    ConfigManager.initialize()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)

    window = AcouZApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
