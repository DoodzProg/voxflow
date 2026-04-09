"""
src/voxflow/ui/components.py

Reusable PySide6 UI components for the Voxflow application.

All components read the current theme via the module-level ``_t()`` accessor
imported from ``voxflow.ui.app_state``. Styling is fully delegated to
``voxflow.ui.styles``.
"""

from __future__ import annotations

import queue
import threading
import time
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QFrame, QScrollArea, QComboBox, QSizePolicy,
)
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, Property,
    QTimer, Signal, QByteArray, QThread,
)
from PySide6.QtSvgWidgets import QSvgWidget

import voxflow.ui.styles as S
from voxflow.ui.styles import ICONS, Theme
from voxflow.utils.config import ConfigManager


# ─────────────────────────────────────────────────────────────
#  THEME STATE ACCESSOR
#  Kept in this module so every component always reads the live theme.
# ─────────────────────────────────────────────────────────────

_dark_mode: bool = True
_theme: Theme = S.DARK


def _t() -> Theme:
    """Return the currently active :class:`~voxflow.ui.styles.Theme` object.

    Returns:
        The global ``DARK`` or ``LIGHT`` theme instance.
    """
    return _theme


def set_theme(dark: bool) -> None:
    """Update the module-level theme state.

    Called exclusively by :meth:`VoxflowApp.apply_theme` before any
    ``retheme()`` call propagates to child pages.

    Args:
        dark: ``True`` to activate DARK mode, ``False`` for LIGHT mode.
    """
    global _dark_mode, _theme
    _dark_mode = dark
    _theme = S.DARK if dark else S.LIGHT


# ─────────────────────────────────────────────────────────────
#  SVG HELPERS
# ─────────────────────────────────────────────────────────────

def _svg_data(key: str, color: str) -> bytes:
    """Build raw SVG bytes for the given icon key and stroke colour.

    Args:
        key:   Key into the :data:`~voxflow.ui.styles.ICONS` dictionary.
        color: CSS colour string used as the SVG stroke value.

    Returns:
        UTF-8 encoded SVG document as bytes.
    """
    body = ICONS.get(key, "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round">{body}</svg>'
    ).encode()


def make_svg(key: str, size: int, color: str) -> QSvgWidget:
    """Create a fixed-size, transparent SVG widget from the icon dictionary.

    Args:
        key:   Icon key defined in :data:`~voxflow.ui.styles.ICONS`.
        size:  Width and height in pixels (square widget).
        color: Stroke colour for the SVG paths.

    Returns:
        A :class:`~PySide6.QtSvgWidgets.QSvgWidget` ready to embed in a layout.
    """
    w = QSvgWidget()
    w.load(QByteArray(_svg_data(key, color)))
    w.setFixedSize(size, size)
    w.setStyleSheet("background: transparent;")
    return w


def reload_svg(widget: QSvgWidget, key: str, color: str) -> None:
    """Reload an existing SVG widget with a new icon key and/or colour.

    Args:
        widget: The :class:`~PySide6.QtSvgWidgets.QSvgWidget` to update.
        key:    New icon key from :data:`~voxflow.ui.styles.ICONS`.
        color:  New stroke colour string.
    """
    widget.load(QByteArray(_svg_data(key, color)))


def icon_label(key: str, text: str, t: Theme, size: int = 14) -> QWidget:
    """Return a transparent ``QWidget`` composed of ``[SVG icon] + [text label]``.

    Used to replace emoji-prefixed ``QLabel`` strings with proper SVG icons
    that adapt to the active theme.

    Args:
        key:  Icon key from :data:`~voxflow.ui.styles.ICONS`.
        text: Label text shown to the right of the icon.
        t:    Current :class:`~voxflow.ui.styles.Theme` instance for styling.
        size: Icon size in pixels (default ``14``).

    Returns:
        A transparent :class:`~PySide6.QtWidgets.QWidget` with a horizontal layout.
    """
    w = QWidget()
    w.setStyleSheet("background: transparent;")
    row = QHBoxLayout(w)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(6)
    row.addWidget(make_svg(key, size, t.text_1))
    lbl = QLabel(text)
    lbl.setStyleSheet(S.setting_label_style(t))
    row.addWidget(lbl)
    row.addStretch()
    return w


# ─────────────────────────────────────────────────────────────
#  LAYOUT HELPERS
# ─────────────────────────────────────────────────────────────

def section_title(text: str) -> QWidget:
    """Return a labelled horizontal-rule section divider.

    Args:
        text: Section name displayed in upper-case on the left.

    Returns:
        A :class:`~PySide6.QtWidgets.QWidget` with icon + rule layout.
    """
    t = _t()
    w = QWidget()
    w.setStyleSheet("background: transparent;")
    r = QHBoxLayout(w)
    r.setContentsMargins(0, 4, 0, 4)
    r.setSpacing(10)
    lbl = QLabel(text.upper())
    lbl.setStyleSheet(S.section_title_style(t))
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet(S.hline_qss(t))
    r.addWidget(lbl)
    r.addWidget(line, 1)
    # Store label reference for retranslation without a custom class.
    w._title_lbl = lbl  # type: ignore[attr-defined]
    return w


def hline() -> QFrame:
    """Return a 1 px hairline horizontal separator.

    Returns:
        A styled :class:`~PySide6.QtWidgets.QFrame` with HLine shape.
    """
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setStyleSheet(S.hline_qss(_t()))
    return f


def page_title(text: str) -> QLabel:
    """Return a styled page heading label.

    Args:
        text: Heading text to display.

    Returns:
        A :class:`~PySide6.QtWidgets.QLabel` with page-title styling.
    """
    lbl = QLabel(text)
    lbl.setStyleSheet(S.page_title_style(_t()))
    return lbl


def card() -> QFrame:
    """Return a borderless rounded card :class:`~PySide6.QtWidgets.QFrame`.

    Returns:
        An unstyled :class:`~PySide6.QtWidgets.QFrame` with card QSS applied.
    """
    f = QFrame()
    f.setStyleSheet(S.card_qss(_t()))
    return f


def btn_primary(text: str) -> QPushButton:
    """Return a filled primary-action button.

    Args:
        text: Button label.

    Returns:
        A :class:`~PySide6.QtWidgets.QPushButton` with primary styling.
    """
    b = QPushButton(text)
    b.setFixedHeight(36)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(S.btn_primary_qss(_t()))
    return b


def btn_ghost(text: str) -> QPushButton:
    """Return a ghost secondary-action button.

    Args:
        text: Button label.

    Returns:
        A :class:`~PySide6.QtWidgets.QPushButton` with ghost styling.
    """
    b = QPushButton(text)
    b.setFixedHeight(36)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(S.btn_ghost_qss(_t()))
    return b


def scrollable(inner: QWidget) -> QScrollArea:
    """Wrap a widget in a borderless, vertically-scrollable area.

    Args:
        inner: The widget to embed inside the scroll area.

    Returns:
        A :class:`~PySide6.QtWidgets.QScrollArea` with transparent background.
    """
    s = QScrollArea()
    s.setWidget(inner)
    s.setWidgetResizable(True)
    s.setStyleSheet("QScrollArea { background: transparent; border: none; }")
    s.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    return s


# ─────────────────────────────────────────────────────────────
#  PILL BADGE
# ─────────────────────────────────────────────────────────────

class PillBadge(QLabel):
    """Small pill-shaped badge label with a configurable accent colour.

    Args:
        text:   Badge text.
        color:  Accent colour hex string (e.g. ``"#7C6FEB"``).
        parent: Optional parent widget.
    """

    def __init__(self, text: str, color: str,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
        self._color = color
        self.setStyleSheet(S.pill_badge_qss(color))
        self.setFixedHeight(20)


# ─────────────────────────────────────────────────────────────
#  TOGGLE SWITCH
# ─────────────────────────────────────────────────────────────

class ToggleSwitch(QWidget):
    """Animated on/off toggle switch.

    Emits :attr:`toggled` with the new boolean state whenever the user clicks.

    Args:
        checked: Initial checked state (default ``False``).
        parent:  Optional parent widget.
    """

    toggled = Signal(bool)

    def __init__(self, checked: bool = False,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(44, 24)
        self.setCursor(Qt.PointingHandCursor)
        self.__t: float = 22.0 if checked else 4.0
        self._anim = QPropertyAnimation(self, b"thumbPos")
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def _get(self) -> float:
        return self.__t

    def _set(self, v: float) -> None:
        self.__t = v
        self.update()

    thumbPos = Property(float, _get, _set)

    def mousePressEvent(self, _) -> None:  # type: ignore[override]
        """Toggle state and start slide animation on mouse press."""
        self._checked = not self._checked
        self._anim.setStartValue(self.__t)
        self._anim.setEndValue(22.0 if self._checked else 4.0)
        self._anim.start()
        self.toggled.emit(self._checked)

    def paintEvent(self, _) -> None:  # type: ignore[override]
        """Render the toggle track and thumb using the current theme colours."""
        t = _t()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(t.accent if self._checked else t.text_3))
        p.drawRoundedRect(0, 2, 44, 20, 10, 10)
        p.setBrush(QColor("white"))
        p.drawEllipse(int(self.__t), 4, 16, 16)
        p.end()


# ─────────────────────────────────────────────────────────────
#  NAV BUTTON
# ─────────────────────────────────────────────────────────────

class NavButton(QPushButton):
    """Sidebar navigation button with an animated active-indicator bar.

    Args:
        icon_key: Key in :data:`~voxflow.ui.styles.ICONS` for the button icon.
        label:    Text label shown next to the icon.
        parent:   Optional parent widget.
    """

    def __init__(self, icon_key: str, label: str,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.icon_key = icon_key
        self._active = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44)

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 0, 12, 0)
        row.setSpacing(10)

        t = _t()
        self._bar = QFrame()
        self._bar.setFixedWidth(3)
        self._bar.setFixedHeight(0)
        self._bar.setStyleSheet(f"background: {t.accent}; border-radius: 2px;")

        self._icon_w = make_svg(icon_key, 16, t.text_2)
        self._lbl = QLabel(label)
        self._lbl.setStyleSheet(S.nav_label_style(False, t))

        row.addWidget(self._bar)
        row.addWidget(self._icon_w)
        row.addWidget(self._lbl)
        row.addStretch()

        self._anim = QPropertyAnimation(self._bar, b"minimumHeight")
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._apply(False)

    def set_active(self, active: bool) -> None:
        """Switch into active or inactive visual state.

        Args:
            active: ``True`` to display the active-indicator bar.
        """
        self._active = active
        self._anim.setEndValue(20 if active else 0)
        self._anim.start()
        self._apply(active)

    def set_label(self, text: str) -> None:
        """Update the text label of the navigation button.

        Args:
            text: New label string (e.g. the translated nav item name).
        """
        self._lbl.setText(text)

    def retheme(self) -> None:
        """Re-apply colours from the current global theme without changing active state."""
        t = _t()
        self._bar.setStyleSheet(f"background: {t.accent}; border-radius: 2px;")
        self._apply(self._active)

    def _apply(self, active: bool) -> None:
        """Internal helper — update QSS and icon colour for ``active`` state.

        Args:
            active: Whether this button is currently the selected page.
        """
        t = _t()
        self.setStyleSheet(S.nav_button_qss(active, t))
        reload_svg(self._icon_w, self.icon_key,
                   t.accent_light if active else t.text_2)
        self._lbl.setStyleSheet(S.nav_label_style(active, t))


# ─────────────────────────────────────────────────────────────
#  SETTING ROW / CARD
# ─────────────────────────────────────────────────────────────

class SettingRow(QWidget):
    """A single labelled row inside a :class:`SettingCard`.

    Args:
        label:   Primary label text.
        desc:    Secondary description text shown below the label.
        control: Right-aligned control widget (toggle, combo, button…).
        parent:  Optional parent widget.
    """

    def __init__(self, label: str, desc: str, control: QWidget,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        t = _t()
        self.setStyleSheet("background: transparent;")
        r = QHBoxLayout(self)
        r.setContentsMargins(20, 14, 20, 14)
        r.setSpacing(12)
        col = QVBoxLayout()
        col.setSpacing(2)
        self._lbl = QLabel(label)
        self._lbl.setStyleSheet(S.setting_label_style(t))
        self._desc = QLabel(desc)
        self._desc.setStyleSheet(S.setting_desc_style(t))
        col.addWidget(self._lbl)
        col.addWidget(self._desc)
        r.addLayout(col, 1)
        r.addWidget(control, 0, Qt.AlignRight | Qt.AlignVCenter)

    def set_texts(self, label: str, desc: str) -> None:
        """Update the label and description text of this row.

        Args:
            label: New primary label string.
            desc:  New description string.
        """
        self._lbl.setText(label)
        self._desc.setText(desc)

    def retheme(self, t: "Theme") -> None:  # noqa: F821
        """Re-apply label styles from the supplied theme.

        Args:
            t: Active :class:`~voxflow.ui.styles.Theme` instance.
        """
        self._lbl.setStyleSheet(S.setting_label_style(t))
        self._desc.setStyleSheet(S.setting_desc_style(t))


class SettingCard(QFrame):
    """Grouped card holding :class:`SettingRow` entries separated by hairlines.

    Args:
        parent: Optional parent widget.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(S.card_qss(_t()))
        self._vbox = QVBoxLayout(self)
        self._vbox.setContentsMargins(0, 0, 0, 0)
        self._vbox.setSpacing(0)
        self._n: int = 0

    def add(self, label: str, desc: str, control: QWidget) -> None:
        """Append a :class:`SettingRow`, inserting a hairline separator if needed.

        Args:
            label:   Primary label for the row.
            desc:    Description text shown below the label.
            control: Widget placed on the right side of the row.
        """
        if self._n:
            self._vbox.addWidget(hline())
        self._vbox.addWidget(SettingRow(label, desc, control))
        self._n += 1

    def rows(self) -> list["SettingRow"]:
        """Return the ordered list of :class:`SettingRow` children.

        Returns:
            All ``SettingRow`` instances currently in the card, in insertion order.
        """
        result: list[SettingRow] = []
        for i in range(self._vbox.count()):
            item = self._vbox.itemAt(i)
            w = item.widget() if item else None
            if isinstance(w, SettingRow):
                result.append(w)
        return result

    def retheme(self, t: "Theme") -> None:  # noqa: F821
        """Re-apply card background and all child row styles.

        Args:
            t: Active :class:`~voxflow.ui.styles.Theme` instance.
        """
        self.setStyleSheet(S.card_qss(t))
        for i in range(self._vbox.count()):
            item = self._vbox.itemAt(i)
            w = item.widget() if item else None
            if isinstance(w, SettingRow):
                w.retheme(t)
            elif isinstance(w, QFrame):          # hairline separator
                w.setStyleSheet(S.hline_qss(t))


# ─────────────────────────────────────────────────────────────
#  STAT CARD
# ─────────────────────────────────────────────────────────────

class StatCard(QFrame):
    """Compact metric card for the dashboard page.

    Args:
        icon_key: Icon key from :data:`~voxflow.ui.styles.ICONS`.
        value:    Initial metric value string (e.g. ``"0 mots"``).
        label:    Descriptive sub-label (e.g. ``"Dictés aujourd'hui"``).
        parent:   Optional parent widget.
    """

    def __init__(self, icon_key: str, value: str, label: str,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        t = _t()
        self.setFixedHeight(88)
        self.setStyleSheet(S.stat_card_qss(t))
        v = QVBoxLayout(self)
        v.setContentsMargins(18, 14, 18, 14)
        v.setSpacing(4)
        top = QHBoxLayout()
        ic = make_svg(icon_key, 16, t.text_3)
        top.addWidget(ic)
        top.addStretch()
        self._val_label = QLabel(value)
        self._val_label.setStyleSheet(
            f"color: {t.text_1}; font-size: 20px; font-weight: 700; "
            f"font-family: 'Segoe UI'; background: transparent;"
        )
        self._sub_label = QLabel(label)
        self._sub_label.setStyleSheet(
            f"color: {t.text_2}; font-size: 11px; "
            f"font-family: 'Segoe UI'; background: transparent;"
        )
        v.addLayout(top)
        v.addWidget(self._val_label)
        v.addWidget(self._sub_label)

    def set_value(self, text: str) -> None:
        """Update the metric value displayed on the card.

        Args:
            text: New value string to display.
        """
        self._val_label.setText(text)

    def set_label(self, text: str) -> None:
        """Update the descriptive sub-label of the card.

        Args:
            text: New sub-label string.
        """
        self._sub_label.setText(text)

    def retheme(self, t: "Theme") -> None:  # noqa: F821
        """Re-apply card and label styles from the supplied theme.

        Args:
            t: Active :class:`~voxflow.ui.styles.Theme` instance.
        """
        self.setStyleSheet(S.stat_card_qss(t))
        self._val_label.setStyleSheet(
            f"color: {t.text_1}; font-size: 20px; font-weight: 700; "
            f"font-family: 'Segoe UI'; background: transparent;"
        )
        self._sub_label.setStyleSheet(
            f"color: {t.text_2}; font-size: 11px; "
            f"font-family: 'Segoe UI'; background: transparent;"
        )


# ─────────────────────────────────────────────────────────────
#  HOTKEY BUTTON & RECORDER
# ─────────────────────────────────────────────────────────────

class HotkeyRecorder(QThread):
    """Short-lived thread that captures a keyboard combination via ``keyboard``.

    Emits :attr:`recorded` with the captured combo string (e.g. ``"ctrl+shift"``).
    Running in a thread prevents the UI from freezing during the capture wait.

    Args:
        parent: Optional parent :class:`~PySide6.QtCore.QObject`.
    """

    recorded = Signal(str)

    def run(self) -> None:
        """Block until a hotkey combination is pressed, then emit it."""
        import keyboard  # noqa: PLC0415  (local import to avoid circular dep)
        combo = keyboard.read_hotkey(suppress=False)
        self.recorded.emit(combo)


class HotkeyButton(QPushButton):
    """Button that displays the current hotkey chips and allows re-binding.

    Clicking the button starts a :class:`HotkeyRecorder` thread; the next
    key combination pressed by the user is saved via :class:`~voxflow.utils.config.ConfigManager`.

    Args:
        config_key: :class:`~voxflow.utils.config.ConfigManager` key to read/write.
        default:    Default hotkey string if the config key is not set.
        parent:     Optional parent widget.
    """

    def __init__(self, config_key: str = "HOTKEY_DICTATE",
                 default: str = "right ctrl+right shift",
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._config_key = config_key
        hotkey_str = ConfigManager.get(config_key, default)
        self._keys: list[str] = [k.strip().title() for k in hotkey_str.split("+")]
        self._listening = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(46)
        self._render()
        self.clicked.connect(self._toggle)

    def _clear(self) -> None:
        """Remove all child widgets from the button layout."""
        lo = self.layout()
        if lo:
            while lo.count():
                item = lo.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        else:
            lo = QHBoxLayout(self)
            # Vertical margins give the key chips breathing room so they
            # never touch the top/bottom border of the button frame.
            lo.setContentsMargins(14, 8, 14, 8)
            lo.setSpacing(8)

    def _render(self) -> None:
        """Rebuild the button's internal layout for the current state."""
        self._clear()
        t = _t()
        lo = self.layout()
        if self._listening:
            dot = QLabel("●")
            dot.setStyleSheet(
                f"color: {t.danger}; font-size: 11px; background: transparent;"
            )
            from voxflow.utils.i18n import tr as _tr  # noqa: PLC0415
            txt = QLabel(_tr("general.hk.listening"))
            txt.setStyleSheet(
                f"color: {t.text_2}; font-size: 13px; "
                f"font-family: 'Segoe UI'; background: transparent;"
            )
            lo.addWidget(dot)
            lo.addWidget(txt)
            lo.addStretch()
            self.setStyleSheet(S.hotkey_listening_qss(t))
        else:
            for k in self._keys:
                chip = QLabel(k)
                chip.setAlignment(Qt.AlignCenter)
                chip.setStyleSheet(S.hotkey_chip_style(t))
                # AlignVCenter prevents the label from expanding to the full
                # button height, keeping the chip compact inside the frame.
                lo.addWidget(chip, 0, Qt.AlignVCenter)
                if k != self._keys[-1]:
                    plus = QLabel("+")
                    plus.setStyleSheet(
                        f"color: {t.text_3}; background: transparent; padding: 0 2px;"
                    )
                    lo.addWidget(plus)
            lo.addStretch()
            from voxflow.utils.i18n import tr as _tr  # noqa: PLC0415
            edit = QLabel(_tr("general.hk.edit"))
            edit.setStyleSheet(
                f"color: {t.text_3}; font-size: 11px; "
                f"font-family: 'Segoe UI'; background: transparent;"
            )
            lo.addWidget(edit)
            self.setStyleSheet(S.hotkey_idle_qss(t))

    def _toggle(self) -> None:
        """Start listening mode or stop it if already active."""
        if not self._listening:
            self._listening = True
            self._render()
            self.recorder = HotkeyRecorder(self)
            self.recorder.recorded.connect(self._on_recorded)
            self.recorder.start()
        else:
            self._stop()

    def _on_recorded(self, combo: str) -> None:
        """Handle a newly captured hotkey combination.

        Args:
            combo: Raw combo string from ``keyboard.read_hotkey()``.
        """
        self._listening = False
        if combo:
            ConfigManager.set(self._config_key, combo)
            self._keys = [k.strip().title() for k in combo.split("+")]
            from PySide6.QtWidgets import QMainWindow  # noqa: PLC0415
            main_win = self.window()
            if isinstance(main_win, QMainWindow) and hasattr(
                main_win, "refresh_home_shortcuts"
            ):
                main_win.refresh_home_shortcuts()
        self._render()

    def _stop(self) -> None:
        """Cancel an in-progress hotkey capture."""
        if self._listening:
            self._listening = False
            if hasattr(self, "recorder") and self.recorder.isRunning():
                self.recorder.terminate()
            self._render()


# ─────────────────────────────────────────────────────────────
#  STYLED COMBO BOX
# ─────────────────────────────────────────────────────────────

class StyledComboBox(QComboBox):
    """QComboBox subclass that paints a custom chevron arrow.

    The native ``::down-arrow`` is hidden via QSS (see ``get_qss``).
    A smooth chevron is drawn in :meth:`paintEvent` using the current
    theme colour, giving a consistent look across platforms.

    The popup container is patched on first open to remove the native
    rectangular OS border, leaving only the rounded QSS styling visible.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        # Remove the QAbstractItemView's own rectangular frame line.
        self.view().setFrameShape(QFrame.NoFrame)
        self.view().setFrameShadow(QFrame.Plain)
        # Pre-patch the popup container *before* it is first shown so that
        # WA_TranslucentBackground takes full effect (Qt requires the attribute
        # to be set before the native window handle is created on first show).
        container = self.view().parentWidget()
        if container and container is not self:
            container.setWindowFlags(
                Qt.Popup
                | Qt.FramelessWindowHint
                | Qt.NoDropShadowWindowHint
            )
            container.setAttribute(Qt.WA_TranslucentBackground, True)
            container.setStyleSheet("background: transparent;")

    def showPopup(self) -> None:
        """Show the popup and re-apply themed view styles.

        Because the container flags are patched in :meth:`__init__`, no
        hide/show cycle is needed here.  Only the view's QSS is refreshed on
        every open so theme changes (dark ↔ light) are reflected immediately.
        """
        super().showPopup()
        view = self.view()
        if view is None:
            return
        t = _t()
        rgb = t.accent.lstrip("#")
        view.setStyleSheet(
            f"QAbstractItemView {{"
            f"  background: {t.bg_card}; border: 1px solid {t.border};"
            f"  border-radius: 10px; padding: 4px; outline: none;"
            f"  color: {t.text_1};"
            f"}}"
            f"QAbstractItemView::item {{"
            f"  padding: 6px 14px; border-radius: 6px; min-height: 28px;"
            f"}}"
            f"QAbstractItemView::item:hover {{ background: {t.bg_hover}; }}"
            f"QAbstractItemView::item:selected {{"
            f"  background: #33{rgb}; color: {t.text_1};"
            f"}}"
        )

    def paintEvent(self, event) -> None:  # type: ignore[override]
        """Render the combo box then overlay a themed chevron arrow."""
        super().paintEvent(event)

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        t = _t()
        pen = QPen(QColor(t.text_3), 1.6)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

        # Draw a ∨ chevron centred in the drop-down area (rightmost 32 px)
        cx = self.width() - 16
        cy = self.height() // 2
        path = QPainterPath()
        path.moveTo(cx - 4, cy - 2)
        path.lineTo(cx,     cy + 2)
        path.lineTo(cx + 4, cy - 2)
        p.drawPath(path)
        p.end()


# ─────────────────────────────────────────────────────────────
#  CUSTOM TITLE BAR
# ─────────────────────────────────────────────────────────────

class TitleBar(QWidget):
    """Frameless custom title bar with Windows-style SVG control buttons.

    Provides an empty draggable area on the left and three control buttons
    (minimise, maximise/restore, close) aligned to the right.  Drag-to-move
    is delegated to the Win32 ``WM_NCLBUTTONDOWN / HTCAPTION`` message so
    that snapping, Aero-Snap and multi-monitor behaviour all work natively.

    Args:
        parent: The :class:`~PySide6.QtWidgets.QMainWindow` that owns this bar.
    """

    HEIGHT: int = 32

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._win = parent
        self._maximised = False
        self.setFixedHeight(self.HEIGHT)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._build()

    # ------------------------------------------------------------------

    def _build(self) -> None:
        """Build the title-bar layout."""
        t = _t()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Drag area (stretch)
        layout.addStretch(1)

        # Window control buttons
        self._btn_min = self._make_btn("−", self._on_min)
        self._btn_max = self._make_btn("□", self._on_max)
        self._btn_cls = self._make_btn("✕", self._on_close, is_close=True)

        layout.addWidget(self._btn_min)
        layout.addWidget(self._btn_max)
        layout.addWidget(self._btn_cls)

        self._apply_style(t)

    def _make_btn(self, symbol: str, slot, is_close: bool = False) -> QPushButton:
        """Create a single title-bar control button.

        Args:
            symbol:   Unicode glyph displayed on the button.
            slot:     Click callback.
            is_close: If ``True``, the button shows a red hover colour.

        Returns:
            A styled :class:`~PySide6.QtWidgets.QPushButton`.
        """
        btn = QPushButton(symbol)
        btn.setFixedSize(46, self.HEIGHT)
        btn.setCursor(Qt.ArrowCursor)
        btn.setFocusPolicy(Qt.NoFocus)
        btn._is_close = is_close  # type: ignore[attr-defined]
        btn.clicked.connect(slot)
        return btn

    # ------------------------------------------------------------------

    def retheme(self, t: "Theme") -> None:  # noqa: F821
        """Update colours when the application theme changes.

        Args:
            t: Active :class:`~voxflow.ui.styles.Theme` instance.
        """
        self._apply_style(t)

    def _apply_style(self, t: "Theme") -> None:  # noqa: F821
        """Apply QSS to the bar and its buttons.

        Args:
            t: Active theme.
        """
        self.setStyleSheet(f"background: {t.bg_sidebar};")
        base = (
            f"QPushButton {{ background: transparent; color: {t.text_2}; "
            f"border: none; font-size: 14px; }}"
        )
        hover_normal = (
            f"QPushButton:hover {{ background: {t.bg_hover}; color: {t.text_1}; }}"
        )
        hover_close = (
            "QPushButton:hover { background: #C42B1C; color: white; }"
        )
        for btn in (self._btn_min, self._btn_max, self._btn_cls):
            hover = hover_close if btn._is_close else hover_normal  # type: ignore[attr-defined]
            btn.setStyleSheet(base + hover)

    def _update_max_icon(self) -> None:
        """Toggle the maximise button glyph between □ and ❐."""
        self._btn_max.setText("❐" if self._maximised else "□")

    # ------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        """Trigger native Win32 window drag on left-button press in drag area."""
        if event.button() == Qt.LeftButton:
            try:
                import ctypes  # noqa: PLC0415
                ctypes.windll.user32.ReleaseCapture()
                ctypes.windll.user32.SendMessageW(
                    int(self._win.winId()), 0xA1, 2, 0  # WM_NCLBUTTONDOWN, HTCAPTION
                )
            except Exception:
                pass

    # ------------------------------------------------------------------

    def _on_min(self) -> None:
        """Minimise the parent window to the taskbar."""
        self._win.showMinimized()

    def _on_max(self) -> None:
        """Toggle between maximised and normal window state."""
        if self._maximised:
            self._win.showNormal()
        else:
            self._win.showMaximized()
        self._maximised = not self._maximised
        self._update_max_icon()

    def _on_close(self) -> None:
        """Minimise to tray (mirrors :meth:`~voxflow.ui.app.VoxflowApp.closeEvent`)."""
        self._win.close()
