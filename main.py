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


def main() -> None:
    """Bootstrap the AcouZ PySide6 application."""
    # Register AcouZ's own taskbar identity before anything else.
    if not getattr(sys, "frozen", False):
        src_dir = os.path.join(os.path.dirname(__file__), "src")
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)

    from acouz.platform import set_app_user_model_id  # noqa: PLC0415
    set_app_user_model_id()

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
