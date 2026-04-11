"""
AcouZ - Open-source AI voice dictation
Copyright (c) 2025-2026 DoodzProg
Licensed under the MIT License

src/acouz/ui/pages/general.py

General settings page for the AcouZ application.

Covers: keyboard shortcuts (dictation + context), trigger mode (hold/toggle),
startup behaviour, confirmation sound, voice overlay visibility, and
language/region preferences (UI language + dictation language).
"""

from __future__ import annotations

import sys
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
)
from PySide6.QtCore import Qt, Signal

import acouz.ui.styles as S
from acouz.ui.styles import Theme
from acouz.ui.components import (
    _t, icon_label, section_title, page_title, card, hline,
    ToggleSwitch, HotkeyButton, SettingCard, StyledComboBox,
)
from acouz.ui.pages.base import BasePage
from acouz.utils.config import ConfigManager
from acouz.utils.i18n import tr


# ---------------------------------------------------------------------------
# Windows startup registry helpers
# ---------------------------------------------------------------------------

_APP_NAME = "AcouZ"


def _startup_cmd() -> str:
    """Return the command string to register in the Run key.

    Returns:
        Quoted executable path; uses ``-m acouz.ui.app`` when running as a
        plain Python interpreter (development mode).
    """
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    return f'"{sys.executable}" -m acouz.ui.app'


def _is_startup_enabled() -> bool:
    """Check whether AcouZ is registered to run at Windows startup.

    Returns:
        ``True`` if the registry value exists under
        ``HKCU\\...\\CurrentVersion\\Run``.
    """
    try:
        import winreg  # noqa: PLC0415
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        )
        winreg.QueryValueEx(key, _APP_NAME)
        winreg.CloseKey(key)
        return True
    except (FileNotFoundError, OSError):
        return False


def _set_startup(enabled: bool) -> None:
    """Add or remove the AcouZ startup registry entry.

    Args:
        enabled: ``True`` to add the entry, ``False`` to remove it.
    """
    import winreg  # noqa: PLC0415

    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_SET_VALUE,
    )
    if enabled:
        winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, _startup_cmd())
    else:
        try:
            winreg.DeleteValue(key, _APP_NAME)
        except FileNotFoundError:
            pass
    winreg.CloseKey(key)


# ---------------------------------------------------------------------------
# Dictation language definitions
# ---------------------------------------------------------------------------

#: Ordered list of (ISO-639-1 code, display name) pairs shown in the combo.
_DICTATION_LANGS: list[tuple[str, str]] = [
    ("en", "English"),
    ("fr", "Français"),
    ("es", "Español"),
    ("de", "Deutsch"),
    ("it", "Italiano"),
]

#: Ordered list of (ISO-639-1 code, display name) pairs for the UI language.
_UI_LANGS: list[tuple[str, str]] = [
    ("en", "English"),
    ("fr", "Français"),
]


class GeneralPage(BasePage):
    """Settings page for hotkeys, behaviour and language preferences.

    All form controls (combos, toggles, hotkey buttons) preserve their state
    across theme switches because :meth:`retheme` only updates visual styles —
    it never rebuilds or replaces existing widgets.

    Signals:
        language_changed (str): Emitted with the new ISO-639-1 UI language code
                                when the user changes the interface language.

    Args:
        parent: Optional parent widget.
    """

    #: Emitted when the user selects a new interface language.
    language_changed: Signal = Signal(str)

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

        self._page_title_lbl = page_title(tr("general.title"))
        root.addWidget(self._page_title_lbl)

        # ── Hotkeys card ─────────────────────────────────────────────
        self._sec_hotkeys = section_title(tr("general.section.hotkeys"))
        root.addWidget(self._sec_hotkeys)
        self._hk_card = card()
        hkv = QVBoxLayout(self._hk_card)
        hkv.setContentsMargins(20, 18, 20, 18)
        hkv.setSpacing(14)

        self._hk_desc = QLabel(tr("general.hk.desc"))
        self._hk_desc.setStyleSheet(S.setting_desc_style(t))
        self._hk_desc.setWordWrap(True)
        hkv.addWidget(self._hk_desc)

        # Dictation shortcut -----------------------------------------
        self._lbl_dictate = icon_label("mic", tr("general.hk.dictate"), t, size=14)
        hkv.addWidget(self._lbl_dictate)
        self._hk_btn_dictate = HotkeyButton(
            config_key="HOTKEY_DICTATE", default="right ctrl+right shift"
        )
        hkv.addWidget(self._hk_btn_dictate)

        mr_dictate = QHBoxLayout()
        self._mode_dictate_lbl = QLabel(tr("general.hk.mode"))
        self._mode_dictate_lbl.setStyleSheet(S.setting_desc_style(t))
        self._mode_dictate_combo = StyledComboBox()
        self._mode_dictate_combo.addItems(
            [tr("general.hk.mode.hold"), tr("general.hk.mode.toggle")]
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
        self._lbl_context = icon_label("zap", tr("general.hk.context"), t, size=14)
        hkv.addWidget(self._lbl_context)
        self._hk_btn_context = HotkeyButton(
            config_key="HOTKEY_CONTEXT", default="right alt+right shift"
        )
        hkv.addWidget(self._hk_btn_context)

        mr_context = QHBoxLayout()
        self._mode_context_lbl = QLabel(tr("general.hk.mode"))
        self._mode_context_lbl.setStyleSheet(S.setting_desc_style(t))
        self._mode_context_combo = StyledComboBox()
        self._mode_context_combo.addItems(
            [tr("general.hk.mode.hold"), tr("general.hk.mode.toggle")]
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
        self._sec_behaviour = section_title(tr("general.section.behaviour"))
        root.addWidget(self._sec_behaviour)
        self._beh_card = SettingCard()

        self._startup_switch = ToggleSwitch(_is_startup_enabled())
        self._startup_switch.toggled.connect(_set_startup)
        self._beh_card.add(
            tr("general.startup.label"),
            tr("general.startup.desc"),
            self._startup_switch,
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
            tr("general.sound.label"),
            tr("general.sound.desc"),
            self._sound_switch,
        )

        self._overlay_switch = ToggleSwitch(
            ConfigManager.get("SHOW_OVERLAY", "true") == "true"
        )
        self._overlay_switch.toggled.connect(
            lambda v: ConfigManager.set(
                "SHOW_OVERLAY", "true" if v else "false"
            )
        )
        self._beh_card.add(
            tr("general.overlay.label"),
            tr("general.overlay.desc"),
            self._overlay_switch,
        )

        root.addWidget(self._beh_card)

        # ── Language card ────────────────────────────────────────────
        self._sec_language = section_title(tr("general.section.language"))
        root.addWidget(self._sec_language)
        self._lang_card = SettingCard()

        # Dictation language combo ------------------------------------
        self._dictation_lang_combo = StyledComboBox()
        for code, name in _DICTATION_LANGS:
            self._dictation_lang_combo.addItem(name, userData=code)
        saved_dict_lang = ConfigManager.get("DICTATION_LANGUAGE", "en")
        self._dictation_lang_combo.setCurrentIndex(
            self._index_for_code(self._dictation_lang_combo, saved_dict_lang)
        )
        self._dictation_lang_combo.currentIndexChanged.connect(
            lambda i: ConfigManager.set(
                "DICTATION_LANGUAGE",
                self._dictation_lang_combo.itemData(i) or "en",
            )
        )
        self._lang_card.add(
            tr("general.lang.dictation.label"),
            tr("general.lang.dictation.desc"),
            self._dictation_lang_combo,
        )

        # UI language combo -------------------------------------------
        self._ui_lang_combo = StyledComboBox()
        for code, name in _UI_LANGS:
            self._ui_lang_combo.addItem(name, userData=code)
        saved_ui_lang = ConfigManager.get("UI_LANGUAGE", "en")
        self._ui_lang_combo.setCurrentIndex(
            self._index_for_code(self._ui_lang_combo, saved_ui_lang)
        )
        self._ui_lang_combo.currentIndexChanged.connect(self._on_ui_lang_changed)
        self._lang_card.add(
            tr("general.lang.ui.label"),
            tr("general.lang.ui.desc"),
            self._ui_lang_combo,
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
            t: New :class:`~acouz.ui.styles.Theme` to apply.
        """
        self._inner.setStyleSheet("background: transparent;")
        self._page_title_lbl.setStyleSheet(S.page_title_style(t))
        self._hk_card.setStyleSheet(S.card_qss(t))
        self._hk_desc.setStyleSheet(S.setting_desc_style(t))
        self._mode_dictate_lbl.setStyleSheet(S.setting_desc_style(t))
        self._mode_context_lbl.setStyleSheet(S.setting_desc_style(t))
        self._beh_card.retheme(t)
        self._lang_card.retheme(t)

        # Rebuild icon-label SVG colours
        self._refresh_icon_label(self._lbl_dictate, "mic", tr("general.hk.dictate"), t)
        self._refresh_icon_label(self._lbl_context, "zap", tr("general.hk.context"), t)

        # HotkeyButtons re-render via _render() which calls _t() internally
        self._hk_btn_dictate._render()
        self._hk_btn_context._render()

    def retranslate(self) -> None:
        """Update all visible text strings to the current UI language."""
        self._page_title_lbl.setText(tr("general.title"))
        self._sec_hotkeys._title_lbl.setText(tr("general.section.hotkeys").upper())
        self._hk_desc.setText(tr("general.hk.desc"))
        self._mode_dictate_lbl.setText(tr("general.hk.mode"))
        self._mode_context_lbl.setText(tr("general.hk.mode"))

        # Rebuild trigger-mode combo items without losing current selection
        self._retranslate_mode_combo(self._mode_dictate_combo)
        self._retranslate_mode_combo(self._mode_context_combo)

        self._sec_behaviour._title_lbl.setText(
            tr("general.section.behaviour").upper()
        )
        beh_rows = self._beh_card.rows()
        if len(beh_rows) >= 3:
            beh_rows[0].set_texts(tr("general.startup.label"), tr("general.startup.desc"))
            beh_rows[1].set_texts(tr("general.sound.label"),   tr("general.sound.desc"))
            beh_rows[2].set_texts(tr("general.overlay.label"), tr("general.overlay.desc"))

        self._sec_language._title_lbl.setText(
            tr("general.section.language").upper()
        )
        lang_rows = self._lang_card.rows()
        if len(lang_rows) >= 2:
            lang_rows[0].set_texts(
                tr("general.lang.dictation.label"), tr("general.lang.dictation.desc")
            )
            lang_rows[1].set_texts(
                tr("general.lang.ui.label"), tr("general.lang.ui.desc")
            )

        # Refresh icon label text
        t = _t()
        self._refresh_icon_label(self._lbl_dictate, "mic", tr("general.hk.dictate"), t)
        self._refresh_icon_label(self._lbl_context, "zap", tr("general.hk.context"), t)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _index_for_code(combo: StyledComboBox, code: str) -> int:
        """Return the combo index whose ``userData`` matches *code*, or 0.

        Args:
            combo: The combo box to search.
            code:  ISO-639-1 language code.

        Returns:
            Matching index, or ``0`` if not found.
        """
        for i in range(combo.count()):
            if combo.itemData(i) == code:
                return i
        return 0

    def _retranslate_mode_combo(self, combo: StyledComboBox) -> None:
        """Re-populate a trigger-mode combo with translated items.

        Preserves the current selection index so the saved config is unchanged.

        Args:
            combo: The trigger-mode combo to retranslate.
        """
        idx = combo.currentIndex()
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(
            [tr("general.hk.mode.hold"), tr("general.hk.mode.toggle")]
        )
        combo.setCurrentIndex(idx)
        combo.blockSignals(False)

    def _on_ui_lang_changed(self, index: int) -> None:
        """Persist the new UI language and notify the application.

        Args:
            index: Selected index in :attr:`_ui_lang_combo`.
        """
        code = self._ui_lang_combo.itemData(index) or "en"
        ConfigManager.set("UI_LANGUAGE", code)
        self.language_changed.emit(code)

    def _refresh_icon_label(
        self, widget: QWidget, key: str, text: str, t: Theme
    ) -> None:
        """Update the SVG icon colour and label style inside an icon_label widget.

        Args:
            widget: The container widget produced by :func:`~acouz.ui.components.icon_label`.
            key:    Icon key in :data:`~acouz.ui.styles.ICONS`.
            text:   Updated label text.
            t:      Active theme.
        """
        from acouz.ui.components import _svg_data  # noqa: PLC0415
        from PySide6.QtCore import QByteArray          # noqa: PLC0415
        from PySide6.QtSvgWidgets import QSvgWidget    # noqa: PLC0415

        lo = widget.layout()
        if not lo:
            return
        for i in range(lo.count()):
            item = lo.itemAt(i)
            if not item or not item.widget():
                continue
            w = item.widget()
            if isinstance(w, QSvgWidget):
                w.load(QByteArray(_svg_data(key, t.text_1)))
            elif isinstance(w, QLabel):
                w.setText(text)
                w.setStyleSheet(S.setting_label_style(t))
