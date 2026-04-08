"""
src/voxflow/ui/pages/base.py

Abstract base class for all Voxflow application pages.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Optional

from PySide6.QtWidgets import QScrollArea, QWidget

from voxflow.ui.styles import Theme


class BasePage(QScrollArea):
    """Abstract base class for every page widget in :class:`~voxflow.ui.app.VoxflowApp`.

    Each concrete subclass builds its layout once in :meth:`_build` (called from
    ``__init__``) and stores references to all inline-styled widgets.  When the
    user toggles the DARK/LIGHT theme, :meth:`~voxflow.ui.app.VoxflowApp.apply_theme`
    calls :meth:`retheme` on every registered page — updating colours without
    rebuilding the widget tree, thereby preserving user-input state.

    Args:
        parent: Optional parent widget.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.setHorizontalScrollBarPolicy(
            # PySide6 enum imported lazily to keep the module lightweight
            __import__("PySide6.QtCore", fromlist=["Qt"]).Qt.ScrollBarAlwaysOff
        )

    @abstractmethod
    def retheme(self, t: Theme) -> None:
        """Re-apply all inline styles using the supplied theme.

        Implementors must update every widget whose style was set with an
        explicit ``setStyleSheet()`` call during construction.  Widgets whose
        appearance is controlled exclusively by the application-level QSS
        (e.g. ``QComboBox``, ``QScrollBar``) do not need to be touched.

        Args:
            t: The new :class:`~voxflow.ui.styles.Theme` instance to apply.
        """
        ...

    @abstractmethod
    def retranslate(self) -> None:
        """Update all visible text strings to the current UI language.

        Implementors must call :func:`~voxflow.utils.i18n.tr` for every
        user-visible string and apply it to the corresponding widget with
        ``setText()``.  Layout structure and widget references must not be
        altered — only text content changes.

        This method is called by
        :meth:`~voxflow.ui.app.VoxflowApp.retranslate_all` whenever the user
        changes the interface language in the Settings page.
        """
        ...
