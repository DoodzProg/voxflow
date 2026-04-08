"""
src/voxflow/ui/pages/home.py

Dashboard / home page for the Voxflow application.

Displays live statistics (word count, recording time, WPM, sessions) and a
scrollable history of the most recent dictation entries. Shortcut cards are
rebuilt dynamically via :meth:`~voxflow.ui.app.VoxflowApp.refresh_home_shortcuts`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame,
)
from PySide6.QtCore import Qt

import voxflow.ui.styles as S
from voxflow.ui.styles import Theme
from voxflow.ui.components import (
    _t, StatCard, section_title, page_title, btn_ghost,
    make_svg, card,
)
from voxflow.ui.pages.base import BasePage
from voxflow.utils.i18n import tr

if TYPE_CHECKING:
    pass


class HomePage(BasePage):
    """Dashboard page showing statistics, active shortcuts and dictation history.

    The page exposes several public attributes that the parent
    :class:`~voxflow.ui.app.VoxflowApp` writes to directly:

    Attributes:
        stat_words:        :class:`~voxflow.ui.components.StatCard` for word count.
        stat_time:         :class:`~voxflow.ui.components.StatCard` for recording time.
        stat_wpm:          :class:`~voxflow.ui.components.StatCard` for WPM.
        stat_sessions:     :class:`~voxflow.ui.components.StatCard` for session count.
        shortcuts_layout:  :class:`~PySide6.QtWidgets.QVBoxLayout` for shortcut cards.
        history_layout:    :class:`~PySide6.QtWidgets.QVBoxLayout` for history entries.
        history_container: :class:`~PySide6.QtWidgets.QWidget` wrapping the history.
        btn_clear:         :class:`~PySide6.QtWidgets.QPushButton` to clear history.

    Args:
        parent: Optional parent widget.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._build()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build(self) -> None:
        """Build the page layout and initialise all public widget references."""
        t = _t()
        self._inner = QWidget()
        self._inner.setStyleSheet("background: transparent;")
        root = QVBoxLayout(self._inner)
        root.setContentsMargins(36, 36, 36, 36)
        root.setSpacing(26)

        # ── Header ──────────────────────────────────────────────────
        hdr = QHBoxLayout()
        self._page_title = page_title(tr("home.title"))
        hdr.addWidget(self._page_title)
        hdr.addStretch()
        root.addLayout(hdr)

        # ── Stats row ────────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.stat_words = StatCard("mic", f"0 {tr('home.stat.words.unit')}", tr("home.stat.words.label"))
        self.stat_time = StatCard("clock", "0 min", tr("home.stat.time.label"))
        self.stat_wpm = StatCard("zap", f"0 {tr('home.stat.wpm.unit')}", tr("home.stat.wpm.label"))
        self.stat_sessions = StatCard("check", "0", tr("home.stat.sessions.label"))
        for sc in (self.stat_words, self.stat_time,
                   self.stat_wpm, self.stat_sessions):
            stats_row.addWidget(sc)
        root.addLayout(stats_row)

        # ── Active shortcuts (rebuilt externally) ────────────────────
        self._sec_shortcuts = section_title(tr("home.section.shortcuts"))
        root.addWidget(self._sec_shortcuts)
        self.shortcuts_layout = QVBoxLayout()
        self.shortcuts_layout.setSpacing(12)
        root.addLayout(self.shortcuts_layout)

        # ── Recent activity header ───────────────────────────────────
        hdr_ar = QHBoxLayout()
        self._activity_lbl = QLabel(tr("home.section.activity"))
        self._activity_lbl.setStyleSheet(S.section_title_style(t))
        self._activity_line = QFrame()
        self._activity_line.setFrameShape(QFrame.HLine)
        self._activity_line.setStyleSheet(S.hline_qss(t))
        hdr_ar.addWidget(self._activity_lbl)
        hdr_ar.addWidget(self._activity_line, 1)

        self.btn_clear = btn_ghost(tr("home.btn.clear"))
        self.btn_clear.setFixedHeight(26)
        self._apply_clear_btn_style(t)
        hdr_ar.addWidget(self.btn_clear)
        root.addLayout(hdr_ar)

        # ── History list (rebuilt externally) ────────────────────────
        self.history_container = QWidget()
        self.history_container.setStyleSheet("background: transparent;")
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(0, 0, 0, 0)
        self.history_layout.setSpacing(8)
        root.addWidget(self.history_container)
        root.addStretch()

        self.setWidget(self._inner)

    # ------------------------------------------------------------------
    # BasePage contract
    # ------------------------------------------------------------------

    def retheme(self, t: Theme) -> None:
        """Re-apply all inline styles from the supplied theme.

        Also refreshes the section-title hairline and the "Réinitialiser"
        button style, which are not covered by the application-level QSS.

        Args:
            t: New :class:`~voxflow.ui.styles.Theme` to apply.
        """
        self._inner.setStyleSheet("background: transparent;")
        self._page_title.setStyleSheet(S.page_title_style(t))
        self._activity_lbl.setStyleSheet(S.section_title_style(t))
        self._activity_line.setStyleSheet(S.hline_qss(t))
        self._apply_clear_btn_style(t)
        # Stat cards have inline colour styles — update them explicitly
        for sc in (self.stat_words, self.stat_time, self.stat_wpm, self.stat_sessions):
            sc.retheme(t)
        # Stat cards repaint via QPainter which reads _t() at paint time.
        # History items are fully rebuilt by VoxflowApp.refresh_dashboard()
        # which is called right after retheme() in apply_theme().

    def retranslate(self) -> None:
        """Update all visible text strings to the current UI language."""
        self._page_title.setText(tr("home.title"))
        self._sec_shortcuts._title_lbl.setText(tr("home.section.shortcuts").upper())
        self._activity_lbl.setText(tr("home.section.activity"))
        self.btn_clear.setText(tr("home.btn.clear"))
        # Stat card sub-labels
        self.stat_words.set_label(tr("home.stat.words.label"))
        self.stat_time.set_label(tr("home.stat.time.label"))
        self.stat_wpm.set_label(tr("home.stat.wpm.label"))
        self.stat_sessions.set_label(tr("home.stat.sessions.label"))
        # Values that contain a translated unit are updated by refresh_dashboard()
        # which is called right after retranslate() in retranslate_all().

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _apply_clear_btn_style(self, t: Theme) -> None:
        """Apply the "Réinitialiser" ghost-danger button style.

        Args:
            t: Active theme instance.
        """
        self.btn_clear.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {t.text_3}; "
            f"border: 1px solid {t.text_3}; border-radius: 4px; "
            f"font-size: 11px; padding: 0 10px; }} "
            f"QPushButton:hover {{ background: transparent; "
            f"color: {t.danger}; border-color: {t.danger}; }}"
        )
