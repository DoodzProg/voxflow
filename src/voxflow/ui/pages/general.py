"""
src/voxflow/ui/pages/general.py

General settings page for the Voxflow application.

Covers: keyboard shortcuts (dictation + context), trigger mode (hold/toggle),
startup behaviour, confirmation sound, and language/region.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox,
)
from PySide6.QtCore import Qt

import voxflow.ui.styles as S
from voxflow.ui.styles import Theme
from voxflow.ui.components import (
    _t, icon_label, section_title, page_title, card, hline,
    ToggleSwitch, HotkeyButton, SettingCard,
)
from voxflow.ui.pages.base import BasePage
from voxflow.utils.config import ConfigManager


class GeneralPage(BasePage):
    """Settings page for hotkeys, behaviour and language preferences.

    All form controls (combos, toggles, hotkey buttons) preserve their state
    across theme switches because :meth:`retheme` only updates visual styles —
    it never rebuilds or replaces existing widgets.

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
        """Build the settings page layout."""
        t = _t()
        self._inner = QWidget()
        self._inner.setStyleSheet("background: transparent;")
        root = QVBoxLayout(self._inner)
        root.setContentsMargins(36, 36, 36, 36)
        root.setSpacing(24)

        self._page_title_lbl = page_title("Paramètres")
        root.addWidget(self._page_title_lbl)

        # ── Hotkeys card ─────────────────────────────────────────────
        root.addWidget(section_title("Raccourci clavier"))
        self._hk_card = card()
        hkv = QVBoxLayout(self._hk_card)
        hkv.setContentsMargins(20, 18, 20, 18)
        hkv.setSpacing(14)

        self._hk_desc = QLabel(
            "Cliquez sur un bouton ci-dessous, puis appuyez sur votre combinaison."
        )
        self._hk_desc.setStyleSheet(S.setting_desc_style(t))
        self._hk_desc.setWordWrap(True)
        hkv.addWidget(self._hk_desc)

        # Dictation shortcut -----------------------------------------
        self._lbl_dictate = icon_label("mic", "Dictée simple", t, size=14)
        hkv.addWidget(self._lbl_dictate)
        self._hk_btn_dictate = HotkeyButton(
            config_key="HOTKEY_DICTATE", default="right ctrl+right shift"
        )
        hkv.addWidget(self._hk_btn_dictate)

        mr_dictate = QHBoxLayout()
        self._mode_dictate_lbl = QLabel("Mode de déclenchement")
        self._mode_dictate_lbl.setStyleSheet(S.setting_desc_style(t))
        self._mode_dictate_combo = QComboBox()
        self._mode_dictate_combo.addItems(
            ["Maintien (Push-to-Talk)", "Appui simple (Toggle)"]
        )
        self._mode_dictate_combo.setCurrentIndex(
            0 if ConfigManager.get("HOTKEY_DICTATE_MODE", "hold") == "hold" else 1
        )
        self._mode_dictate_combo.currentIndexChanged.connect(
            lambda i: ConfigManager.set(
                "HOTKEY_DICTATE_MODE", "hold" if i == 0 else "toggle"
            )
        )
        mr_dictate.addWidget(self._mode_dictate_lbl)
        mr_dictate.addStretch()
        mr_dictate.addWidget(self._mode_dictate_combo)
        hkv.addLayout(mr_dictate)

        hkv.addWidget(hline())

        # Context shortcut --------------------------------------------
        self._lbl_context = icon_label("zap", "Instructions avec contexte", t, size=14)
        hkv.addWidget(self._lbl_context)
        self._hk_btn_context = HotkeyButton(
            config_key="HOTKEY_CONTEXT", default="right alt+right shift"
        )
        hkv.addWidget(self._hk_btn_context)

        mr_context = QHBoxLayout()
        self._mode_context_lbl = QLabel("Mode de déclenchement")
        self._mode_context_lbl.setStyleSheet(S.setting_desc_style(t))
        self._mode_context_combo = QComboBox()
        self._mode_context_combo.addItems(
            ["Maintien (Push-to-Talk)", "Appui simple (Toggle)"]
        )
        self._mode_context_combo.setCurrentIndex(
            0 if ConfigManager.get("HOTKEY_CONTEXT_MODE", "hold") == "hold" else 1
        )
        self._mode_context_combo.currentIndexChanged.connect(
            lambda i: ConfigManager.set(
                "HOTKEY_CONTEXT_MODE", "hold" if i == 0 else "toggle"
            )
        )
        mr_context.addWidget(self._mode_context_lbl)
        mr_context.addStretch()
        mr_context.addWidget(self._mode_context_combo)
        hkv.addLayout(mr_context)

        root.addWidget(self._hk_card)

        # ── Behaviour card ───────────────────────────────────────────
        root.addWidget(section_title("Comportement"))
        self._beh_card = SettingCard()
        self._beh_card.add(
            "Démarrage automatique",
            "Lancer Voxflow au démarrage de Windows",
            ToggleSwitch(True),
        )
        self._sound_switch = ToggleSwitch(
            ConfigManager.get("CONFIRMATION_SOUND", "true") == "true"
        )
        self._sound_switch.toggled.connect(
            lambda v: ConfigManager.set(
                "CONFIRMATION_SOUND", "true" if v else "false"
            )
        )
        self._beh_card.add(
            "Son de confirmation",
            "Jouer un son au début et à la fin de la dictée",
            self._sound_switch,
        )
        root.addWidget(self._beh_card)

        # ── Language card ────────────────────────────────────────────
        root.addWidget(section_title("Langue & Région"))
        self._lang_card = SettingCard()
        lc = QComboBox()
        lc.addItems(["Français", "English", "Español", "Deutsch", "Italiano"])
        self._lang_card.add(
            "Langue de dictée",
            "Langue principale utilisée pour la transcription",
            lc,
        )
        ui_lang = QComboBox()
        ui_lang.addItems(["Français", "English"])
        self._lang_card.add(
            "Langue de l'interface",
            "Langue d'affichage de Voxflow",
            ui_lang,
        )
        root.addWidget(self._lang_card)
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
        self._page_title_lbl.setStyleSheet(S.page_title_style(t))
        self._hk_card.setStyleSheet(S.card_qss(t))
        self._hk_desc.setStyleSheet(S.setting_desc_style(t))
        self._mode_dictate_lbl.setStyleSheet(S.setting_desc_style(t))
        self._mode_context_lbl.setStyleSheet(S.setting_desc_style(t))
        self._beh_card.setStyleSheet(S.card_qss(t))
        self._lang_card.setStyleSheet(S.card_qss(t))

        # Rebuild icon-label widgets (they contain inline SVG + label styles)
        self._refresh_icon_label(
            self._lbl_dictate, "mic", "Dictée simple", t
        )
        self._refresh_icon_label(
            self._lbl_context, "zap", "Instructions avec contexte", t
        )

        # HotkeyButtons re-render via _render() which calls _t() internally
        self._hk_btn_dictate._render()
        self._hk_btn_context._render()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _refresh_icon_label(
        self, widget: QWidget, key: str, text: str, t: Theme
    ) -> None:
        """Update the SVG icon colour and label style inside an icon_label widget.

        Args:
            widget: The container widget produced by :func:`~voxflow.ui.components.icon_label`.
            key:    Icon key in :data:`~voxflow.ui.styles.ICONS`.
            text:   Label text (unchanged).
            t:      Active theme.
        """
        from voxflow.ui.components import reload_svg, _svg_data  # noqa: PLC0415
        from PySide6.QtCore import QByteArray  # noqa: PLC0415
        from PySide6.QtSvgWidgets import QSvgWidget  # noqa: PLC0415

        lo = widget.layout()
        if not lo:
            return
        for i in range(lo.count()):
            item = lo.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if isinstance(w, QSvgWidget):
                    w.load(QByteArray(_svg_data(key, t.text_1)))
                elif isinstance(w, QLabel):
                    w.setStyleSheet(S.setting_label_style(t))
