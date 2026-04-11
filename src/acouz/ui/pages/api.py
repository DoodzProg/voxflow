"""
AcouZ - Open-source AI voice dictation
Copyright (c) 2025-2026 DoodzProg
Licensed under the MIT License

src/acouz/ui/pages/api.py

Groq API key configuration page for the AcouZ application.

Allows the user to enter, toggle visibility, verify and save their Groq API key.
The key is stored persistently via :class:`~acouz.utils.config.ConfigManager`.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame,
    QLineEdit, QPushButton, QMessageBox, QApplication,
)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices

import acouz.ui.styles as S
from acouz.ui.styles import Theme
from acouz.ui.components import (
    _t, section_title, page_title, card, btn_primary, btn_ghost,
    make_svg, reload_svg,
)
from acouz.ui.pages.base import BasePage
from acouz.utils.config import ConfigManager
from acouz.utils.i18n import tr


class ApiPage(BasePage):
    """Groq API key configuration page.

    Provides a password-masked input, an eye-toggle for visibility, a
    "Verify key" button that performs a live ``models.list()`` probe, and a
    "Save" button that persists the key to ``.env``.

    Args:
        parent: Optional parent widget.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._vis: bool = False
        self._build()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build(self) -> None:
        """Build the API key page layout."""
        t = _t()
        self._inner = QWidget()
        self._inner.setStyleSheet("background: transparent;")
        root = QVBoxLayout(self._inner)
        root.setContentsMargins(36, 36, 36, 36)
        root.setSpacing(24)

        self._page_title_lbl = page_title(tr("api.title"))
        root.addWidget(self._page_title_lbl)

        # ── Info banner ──────────────────────────────────────────────
        self._banner = QFrame()
        self._banner.setStyleSheet(S.api_banner_qss(t))
        br = QHBoxLayout(self._banner)
        br.setContentsMargins(16, 12, 16, 12)
        br.setSpacing(12)
        self._banner_icon = make_svg("info", 16, t.accent_light)
        br.addWidget(self._banner_icon)
        self._banner_lbl = QLabel(tr("api.banner"))
        self._banner_lbl.setStyleSheet(S.setting_desc_style(t))
        self._banner_lbl.setWordWrap(True)
        br.addWidget(self._banner_lbl, 1)
        root.addWidget(self._banner)

        self._sec_config = section_title(tr("api.section"))
        root.addWidget(self._sec_config)

        # ── Form card ────────────────────────────────────────────────
        self._form = card()
        fv = QVBoxLayout(self._form)
        fv.setContentsMargins(22, 20, 22, 20)
        fv.setSpacing(14)

        # Label row: "Groq API Key" on left, "Get a free API key →" link on right
        lbl_row = QHBoxLayout()
        lbl_row.setSpacing(8)
        self._api_lbl = QLabel(tr("api.key.label"))
        self._api_lbl.setStyleSheet(S.setting_label_style(t))
        lbl_row.addWidget(self._api_lbl, 1)
        self._free_key_btn = QPushButton(tr("api.get.free.key"))
        self._free_key_btn.setCursor(Qt.PointingHandCursor)
        self._free_key_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {t.accent_light}; "
            f"border: none; font-size: 12px; font-family: 'Segoe UI'; "
            f"padding: 0; text-decoration: underline; }} "
            f"QPushButton:hover {{ color: {t.accent}; }}"
        )
        self._free_key_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://console.groq.com/keys"))
        )
        lbl_row.addWidget(self._free_key_btn, 0, Qt.AlignRight | Qt.AlignVCenter)
        fv.addLayout(lbl_row)

        # Input + eye button row
        ir = QHBoxLayout()
        ir.setSpacing(8)
        self._api_input = QLineEdit()
        self._api_input.setText(ConfigManager.get("GROQ_API_KEY", ""))
        self._api_input.setPlaceholderText("gsk_…")
        self._api_input.setEchoMode(QLineEdit.Password)
        self._api_input.setFixedHeight(40)
        self._api_input.setStyleSheet(S.line_edit_qss(t))

        self._eye_btn = QPushButton()
        self._eye_btn.setFixedSize(40, 40)
        self._eye_btn.setCursor(Qt.PointingHandCursor)
        self._eye_btn.setStyleSheet(S.eye_btn_qss(t))
        self._eye_icon = make_svg("eye", 16, t.text_2)
        eye_lo = QHBoxLayout(self._eye_btn)
        eye_lo.setContentsMargins(0, 0, 0, 0)
        eye_lo.addWidget(self._eye_icon, 0, Qt.AlignCenter)
        self._eye_btn.clicked.connect(self._toggle_visibility)

        ir.addWidget(self._api_input, 1)
        ir.addWidget(self._eye_btn)
        fv.addLayout(ir)

        # Action buttons row
        ar = QHBoxLayout()
        ar.addStretch()
        self._btn_verify = btn_ghost(tr("api.btn.verify"))
        self._btn_save = btn_primary(tr("api.btn.save"))
        self._btn_verify.clicked.connect(self._verify_key)
        self._btn_save.clicked.connect(self._save_key)
        ar.addWidget(self._btn_verify)
        ar.addWidget(self._btn_save)
        fv.addLayout(ar)

        root.addWidget(self._form)
        root.addStretch()
        self.setWidget(self._inner)

    # ------------------------------------------------------------------
    # BasePage contract
    # ------------------------------------------------------------------

    def retheme(self, t: Theme) -> None:
        """Re-apply all inline styles using the supplied theme.

        Args:
            t: New :class:`~acouz.ui.styles.Theme` to apply.
        """
        self._inner.setStyleSheet("background: transparent;")
        self._page_title_lbl.setStyleSheet(S.page_title_style(t))
        self._banner.setStyleSheet(S.api_banner_qss(t))
        reload_svg(self._banner_icon, "info", t.accent_light)
        self._banner_lbl.setStyleSheet(S.setting_desc_style(t))
        self._form.setStyleSheet(S.card_qss(t))
        self._api_lbl.setStyleSheet(S.setting_label_style(t))
        self._free_key_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {t.accent_light}; "
            f"border: none; font-size: 12px; font-family: 'Segoe UI'; "
            f"padding: 0; text-decoration: underline; }} "
            f"QPushButton:hover {{ color: {t.accent}; }}"
        )
        self._api_input.setStyleSheet(S.line_edit_qss(t))
        self._eye_btn.setStyleSheet(S.eye_btn_qss(t))
        reload_svg(self._eye_icon, "eye_off" if self._vis else "eye", t.text_2)
        self._btn_verify.setStyleSheet(S.btn_ghost_qss(t))
        self._btn_save.setStyleSheet(S.btn_primary_qss(t))

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _toggle_visibility(self) -> None:
        """Toggle API key input between plain-text and password echo mode."""
        self._vis = not self._vis
        self._api_input.setEchoMode(
            QLineEdit.Normal if self._vis else QLineEdit.Password
        )
        reload_svg(
            self._eye_icon,
            "eye_off" if self._vis else "eye",
            _t().text_2,
        )

    def retranslate(self) -> None:
        """Update all visible text strings to the current UI language."""
        self._page_title_lbl.setText(tr("api.title"))
        self._sec_config._title_lbl.setText(tr("api.section").upper())
        self._banner_lbl.setText(tr("api.banner"))
        self._api_lbl.setText(tr("api.key.label"))
        self._free_key_btn.setText(tr("api.get.free.key"))
        self._btn_verify.setText(tr("api.btn.verify"))
        self._btn_save.setText(tr("api.btn.save"))

    def _verify_key(self) -> None:
        """Perform a live API probe and update the verify button with feedback."""
        key = self._api_input.text().strip()
        if not key:
            self._btn_verify.setText(tr("api.verify.empty"))
            QTimer.singleShot(2000, lambda: self._btn_verify.setText(tr("api.btn.verify")))
            return

        self._btn_verify.setText(tr("api.verify.checking"))
        QApplication.processEvents()

        try:
            from groq import Groq  # noqa: PLC0415
            Groq(api_key=key).models.list()
            self._btn_verify.setText(tr("api.verify.valid"))
        except Exception as exc:
            self._btn_verify.setText(tr("api.verify.invalid"))
            QMessageBox.critical(
                self,
                tr("api.verify.error.title"),
                tr("api.verify.error.msg").format(exc=exc),
            )

        def _reset() -> None:
            self._btn_verify.setText(tr("api.btn.verify"))
            self._btn_verify.setStyleSheet(S.btn_ghost_qss(_t()))

        QTimer.singleShot(2500, _reset)

    def _save_key(self) -> None:
        """Persist the current input value to ``.env`` via ConfigManager."""
        ConfigManager.set("GROQ_API_KEY", self._api_input.text().strip())
        self._btn_save.setText(tr("api.save.done"))
        QTimer.singleShot(2000, lambda: self._btn_save.setText(tr("api.btn.save")))
