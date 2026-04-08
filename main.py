"""
main.py

Application entry point used by both the development runner and PyInstaller.
All heavy imports happen inside the function so that the frozen exe starts
quickly and error messages are not lost before the event loop begins.
"""

import sys
import os


def _set_app_user_model_id() -> None:
    """Tell Windows to treat Voxflow as its own taskbar entity.

    Without this call Windows groups the process under the generic Python
    interpreter icon.  Must be called before any window or QApplication is
    created so the Shell picks up the ID from the very first message pump.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes  # noqa: PLC0415
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "DoodzProg.Voxflow.1.0"
        )
    except Exception:
        pass  # Non-fatal — the app still works, just with the Python icon.


def main() -> None:
    """Bootstrap the Voxflow PySide6 application."""
    # Register Voxflow's own taskbar identity before anything else.
    _set_app_user_model_id()

    # When running from a PyInstaller bundle (_MEIPASS is set), the bundled
    # packages are already on sys.path.  In development we add src/ manually.
    if not getattr(sys, "frozen", False):
        src_dir = os.path.join(os.path.dirname(__file__), "src")
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)

    from voxflow.utils.config import ConfigManager  # noqa: PLC0415
    from voxflow.ui.app import VoxflowApp            # noqa: PLC0415
    from PySide6.QtWidgets import QApplication       # noqa: PLC0415

    ConfigManager.initialize()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)

    window = VoxflowApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
