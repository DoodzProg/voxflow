"""
src/voxflow/ui/pages/about.py

About page for the Voxflow application.

Displays the application logo, version information, and external links
(GitHub, bug reports, feature requests).
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame,
)
from PySide6.QtCore import Qt

import voxflow.ui.styles as S
from voxflow.ui.styles import Theme
from voxflow.ui.components import (
    _t, section_title, hline, btn_ghost,
    make_svg, reload_svg, PillBadge, SettingCard,
)
from voxflow.ui.pages.base import BasePage


class AboutPage(BasePage):
    """About page showing version, environment and project links.

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
        """Build the about page layout."""
        t = _t()
        self._inner = QWidget()
        self._inner.setStyleSheet("background: transparent;")
        root = QVBoxLayout(self._inner)
        root.setContentsMargins(36, 36, 36, 36)
        root.setSpacing(24)
        root.setAlignment(Qt.AlignTop)

        # ── Logo + title row ─────────────────────────────────────────
        lr = QHBoxLayout()
        lr.setSpacing(16)
        lr.setAlignment(Qt.AlignLeft)

        self._logo_bg = QFrame()
        self._logo_bg.setFixedSize(52, 52)
        self._logo_bg.setStyleSheet(S.about_logo_qss(t))
        self._logo_mic = make_svg("mic", 26, "white")
        self._logo_mic.setParent(self._logo_bg)
        self._logo_mic.setGeometry(13, 13, 26, 26)

        nc = QVBoxLayout()
        nc.setSpacing(2)
        self._app_name = QLabel("Voxflow")
        self._app_name.setStyleSheet(
            f"color: {t.text_1}; font-size: 26px; font-weight: 700; "
            f"font-family: 'Segoe UI'; background: transparent;"
        )
        self._app_tagline = QLabel(
            "Dictée vocale open-source. Rapide, privée, gratuite."
        )
        self._app_tagline.setStyleSheet(
            f"color: {t.text_2}; font-size: 13px; "
            f"font-family: 'Segoe UI'; background: transparent;"
        )
        nc.addWidget(self._app_name)
        nc.addWidget(self._app_tagline)
        lr.addWidget(self._logo_bg)
        lr.addLayout(nc)
        lr.addStretch()
        root.addLayout(lr)

        # ── Version card ─────────────────────────────────────────────
        root.addWidget(section_title("Version"))
        self._version_card = SettingCard()
        self._version_badge = PillBadge("v0.4.0-alpha", t.accent)
        self._env_badge = PillBadge("Python 3.12", t.accent_purple)
        self._version_card.add(
            "Version actuelle",
            "Phase 4 — Interface graphique & .exe",
            self._version_badge,
        )
        self._version_card.add(
            "Environnement",
            "Moteur de transcription Groq Whisper",
            self._env_badge,
        )
        root.addWidget(self._version_card)

        # ── Links card ───────────────────────────────────────────────
        root.addWidget(section_title("Liens"))
        self._links_card = QFrame()
        self._links_card.setStyleSheet(S.card_qss(t))
        lv = QVBoxLayout(self._links_card)
        lv.setContentsMargins(20, 10, 20, 10)
        lv.setSpacing(0)

        self._link_rows: list[tuple[QLabel, QLabel, QLabel]] = []
        for i, (ik, text, url) in enumerate([
            ("star", "GitHub — Code source et releases", "https://github.com/DoodzProg/voxflow"),
            ("bug",  "Signaler un bug",                  "https://github.com"),
            ("link", "Proposer une fonctionnalité",      "https://github.com"),
        ]):
            if i:
                lv.addWidget(hline())
            rw = QWidget()
            rw.setStyleSheet("background: transparent;")
            rr = QHBoxLayout(rw)
            rr.setContentsMargins(0, 10, 0, 10)
            rr.setSpacing(12)
            ic = make_svg(ik, 15, t.text_3)
            rr.addWidget(ic)
            lnk = QLabel(
                f'<a href="{url}" style="color:{t.text_2}; '
                f'text-decoration:none;">{text}</a>'
            )
            lnk.setOpenExternalLinks(True)
            lnk.setStyleSheet(
                "background: transparent; font-size: 13px; font-family: 'Segoe UI';"
            )
            rr.addWidget(lnk)
            rr.addStretch()
            arrow = make_svg("arrow_r", 13, t.text_3)
            rr.addWidget(arrow)
            lv.addWidget(rw)
            self._link_rows.append((ic, lnk, arrow))

        root.addWidget(self._links_card)

        self._update_btn = btn_ghost("Vérifier les mises à jour")
        root.addWidget(self._update_btn)
        root.addStretch()
        self.setWidget(self._inner)

    # ------------------------------------------------------------------
    # BasePage contract
    # ------------------------------------------------------------------

    def retheme(self, t: Theme) -> None:
        """Re-apply all inline styles using the supplied theme.

        Args:
            t: New :class:`~voxflow.ui.styles.Theme` to apply.
        """
        self._inner.setStyleSheet("background: transparent;")
        self._logo_bg.setStyleSheet(S.about_logo_qss(t))
        self._app_name.setStyleSheet(
            f"color: {t.text_1}; font-size: 26px; font-weight: 700; "
            f"font-family: 'Segoe UI'; background: transparent;"
        )
        self._app_tagline.setStyleSheet(
            f"color: {t.text_2}; font-size: 13px; "
            f"font-family: 'Segoe UI'; background: transparent;"
        )
        self._version_card.setStyleSheet(S.card_qss(t))
        self._version_badge.setStyleSheet(S.pill_badge_qss(t.accent))
        self._env_badge.setStyleSheet(S.pill_badge_qss(t.accent_purple))
        self._links_card.setStyleSheet(S.card_qss(t))
        self._update_btn.setStyleSheet(S.btn_ghost_qss(t))

        # Update link SVG colours and anchor colours
        for i, (ic, lnk, arrow) in enumerate(self._link_rows):
            reload_svg(ic, ["star", "bug", "link"][i], t.text_3)
            # Re-render the anchor with the new text_2 colour
            urls = [
                "https://github.com",
                "https://github.com",
                "https://github.com",
            ]
            texts = [
                "GitHub — Code source et releases",
                "Signaler un bug",
                "Proposer une fonctionnalité",
            ]
            lnk.setText(
                f'<a href="{urls[i]}" style="color:{t.text_2}; '
                f'text-decoration:none;">{texts[i]}</a>'
            )
            reload_svg(arrow, "arrow_r", t.text_3)
