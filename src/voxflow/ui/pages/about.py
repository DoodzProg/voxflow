"""
src/voxflow/ui/pages/about.py

About page for the Voxflow application.

Displays the application logo, version info, project links (GitHub, bug reports,
feature requests) and a button that checks the GitHub Releases API for updates.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame,
)
from PySide6.QtCore import Qt, QThread, Signal, QByteArray
from PySide6.QtSvgWidgets import QSvgWidget

import voxflow.ui.styles as S
from voxflow.ui.styles import Theme, LOGO_SVG
from voxflow.ui.components import (
    _t, section_title, hline, btn_ghost,
    make_svg, reload_svg, PillBadge, SettingCard,
)
from voxflow.ui.pages.base import BasePage
from voxflow.utils.i18n import tr

# Bump this constant when releasing a new version.
_CURRENT_VERSION = "1.0.1"
_REPO = "DoodzProg/voxflow"


class _UpdateChecker(QThread):
    """Background thread that queries the GitHub Releases API.

    Signals:
        result: Emitted with a human-readable status message when done.
    """

    result = Signal(str)

    def run(self) -> None:
        """Fetch the latest release tag from the GitHub API."""
        url = f"https://api.github.com/repos/{_REPO}/releases/latest"
        try:
            req = urllib.request.Request(
                url,
                headers={"Accept": "application/vnd.github+json",
                         "User-Agent": "Voxflow-UpdateChecker/1.0"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                import json  # noqa: PLC0415
                data = json.loads(resp.read())
            tag: str = data.get("tag_name", "").lstrip("v")
            if tag and tag != _CURRENT_VERSION:
                self.result.emit(tr("about.update.available").format(tag=tag))
            else:
                self.result.emit(tr("about.update.uptodate"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                self.result.emit(tr("about.update.noreleases"))
            else:
                self.result.emit(tr("about.update.error").format(code=exc.code))
        except Exception:
            self.result.emit(tr("about.update.unreachable"))


class AboutPage(BasePage):
    """About page showing version, environment and project links.

    Args:
        parent: Optional parent widget.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._update_checker: Optional[_UpdateChecker] = None
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

        # Use the real application logo SVG (gradient background included).
        self._logo_bg = QSvgWidget()
        self._logo_bg.setFixedSize(56, 56)
        self._logo_bg.load(QByteArray(LOGO_SVG.encode()))

        nc = QVBoxLayout()
        nc.setSpacing(2)
        self._app_name = QLabel("Voxflow")
        self._app_name.setStyleSheet(
            f"color: {t.text_1}; font-size: 26px; font-weight: 700; "
            f"font-family: 'Segoe UI Variable', 'Segoe UI'; background: transparent;"
        )
        self._app_tagline = QLabel(tr("about.tagline"))
        self._app_tagline.setStyleSheet(
            f"color: {t.text_2}; font-size: 13px; "
            f"font-family: 'Segoe UI Variable', 'Segoe UI'; background: transparent;"
        )
        nc.addWidget(self._app_name)
        nc.addWidget(self._app_tagline)
        lr.addWidget(self._logo_bg)
        lr.addLayout(nc)
        lr.addStretch()
        root.addLayout(lr)

        # ── Version card ─────────────────────────────────────────────
        self._sec_version = section_title(tr("about.section.version"))
        root.addWidget(self._sec_version)
        self._version_card = SettingCard()
        # Both badges use accent colour so they are legible in dark and light.
        self._version_badge = PillBadge(f"v{_CURRENT_VERSION}", t.accent)
        self._env_badge = PillBadge("Python 3.12", t.accent)
        self._version_card.add(
            tr("about.version.label"),
            tr("about.version.desc"),
            self._version_badge,
        )
        self._version_card.add(
            tr("about.env.label"),
            tr("about.env.desc"),
            self._env_badge,
        )
        root.addWidget(self._version_card)

        # ── Links card ───────────────────────────────────────────────
        self._sec_links = section_title(tr("about.section.links"))
        root.addWidget(self._sec_links)
        self._links_card = QFrame()
        self._links_card.setStyleSheet(S.card_qss(t))
        lv = QVBoxLayout(self._links_card)
        lv.setContentsMargins(20, 10, 20, 10)
        lv.setSpacing(0)

        # (icon_key, tr_key, url)
        _link_defs = [
            (
                "star",
                "about.link.github",
                f"https://github.com/{_REPO}",
            ),
            (
                "bug",
                "about.link.bug",
                f"https://github.com/{_REPO}/issues/new?template=bug_report.md",
            ),
            (
                "link",
                "about.link.feature",
                f"https://github.com/{_REPO}/issues/new?template=feature_request.md",
            ),
        ]
        # Store tr keys and urls separately for retranslation
        self._link_tr_keys = [d[1] for d in _link_defs]
        self._link_urls = [d[2] for d in _link_defs]

        self._link_rows: list[tuple[QWidget, QLabel, QWidget]] = []
        for i, (ik, text_key, url) in enumerate(_link_defs):
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
                f'text-decoration:none;">{tr(text_key)}</a>'
            )
            lnk.setOpenExternalLinks(True)
            lnk.setStyleSheet(
                "background: transparent; font-size: 13px; "
                "font-family: 'Segoe UI Variable', 'Segoe UI';"
            )
            rr.addWidget(lnk)
            rr.addStretch()
            arrow = make_svg("arrow_r", 13, t.text_3)
            rr.addWidget(arrow)
            lv.addWidget(rw)
            self._link_rows.append((ic, lnk, arrow))

        root.addWidget(self._links_card)

        self._update_btn = btn_ghost(tr("about.btn.update"))
        self._update_btn.clicked.connect(self._check_updates)
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
        # QSvgWidget renders its own gradient — no stylesheet needed.
        self._app_name.setStyleSheet(
            f"color: {t.text_1}; font-size: 26px; font-weight: 700; "
            f"font-family: 'Segoe UI Variable', 'Segoe UI'; background: transparent;"
        )
        self._app_tagline.setStyleSheet(
            f"color: {t.text_2}; font-size: 13px; "
            f"font-family: 'Segoe UI Variable', 'Segoe UI'; background: transparent;"
        )
        self._version_card.retheme(t)
        # Both badges always use accent so they remain readable in light mode.
        self._version_badge.setStyleSheet(S.pill_badge_qss(t.accent))
        self._env_badge.setStyleSheet(S.pill_badge_qss(t.accent))
        self._links_card.setStyleSheet(S.card_qss(t))
        self._update_btn.setStyleSheet(S.btn_ghost_qss(t))

        icon_keys = ["star", "bug", "link"]
        for i, (ic, lnk, arrow) in enumerate(self._link_rows):
            reload_svg(ic, icon_keys[i], t.text_3)
            lnk.setText(
                f'<a href="{self._link_urls[i]}" style="color:{t.text_2}; '
                f'text-decoration:none;">{tr(self._link_tr_keys[i])}</a>'
            )
            reload_svg(arrow, "arrow_r", t.text_3)

    def retranslate(self) -> None:
        """Update all visible text strings to the current UI language."""
        self._app_tagline.setText(tr("about.tagline"))
        self._sec_version._title_lbl.setText(tr("about.section.version").upper())
        self._sec_links._title_lbl.setText(tr("about.section.links").upper())
        self._update_btn.setText(tr("about.btn.update"))

        version_rows = self._version_card.rows()
        if len(version_rows) >= 2:
            version_rows[0].set_texts(tr("about.version.label"), tr("about.version.desc"))
            version_rows[1].set_texts(tr("about.env.label"),     tr("about.env.desc"))

        # Re-render link labels with the new language
        t = _t()
        for i, (_ic, lnk, _arrow) in enumerate(self._link_rows):
            lnk.setText(
                f'<a href="{self._link_urls[i]}" style="color:{t.text_2}; '
                f'text-decoration:none;">{tr(self._link_tr_keys[i])}</a>'
            )

    # ------------------------------------------------------------------
    # Update check
    # ------------------------------------------------------------------

    def _check_updates(self) -> None:
        """Start a background thread to query the GitHub Releases API."""
        self._update_btn.setText(tr("about.update.checking"))
        self._update_btn.setEnabled(False)

        self._update_checker = _UpdateChecker(self)
        self._update_checker.result.connect(self._on_update_result)
        self._update_checker.start()

    def _on_update_result(self, message: str) -> None:
        """Display the update-check result on the button.

        Args:
            message: Human-readable status string from :class:`_UpdateChecker`.
        """
        self._update_btn.setText(message)
        self._update_btn.setEnabled(True)
