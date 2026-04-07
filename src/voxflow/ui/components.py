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
    QFrame, QScrollArea, QComboBox,
)
from PySide6.QtGui import QColor, QPainter
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
        l = QLabel(label)
        l.setStyleSheet(S.setting_label_style(t))
        d = QLabel(desc)
        d.setStyleSheet(S.setting_desc_style(t))
        col.addWidget(l)
        col.addWidget(d)
        r.addLayout(col, 1)
        r.addWidget(control, 0, Qt.AlignRight | Qt.AlignVCenter)


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
        sub = QLabel(label)
        sub.setStyleSheet(
            f"color: {t.text_2}; font-size: 11px; "
            f"font-family: 'Segoe UI'; background: transparent;"
        )
        v.addLayout(top)
        v.addWidget(self._val_label)
        v.addWidget(sub)

    def set_value(self, text: str) -> None:
        """Update the metric value displayed on the card.

        Args:
            text: New value string to display.
        """
        self._val_label.setText(text)


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
            lo.setContentsMargins(16, 0, 16, 0)
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
            txt = QLabel("Appuyez sur vos touches...")
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
                lo.addWidget(chip)
                if k != self._keys[-1]:
                    plus = QLabel("+")
                    plus.setStyleSheet(
                        f"color: {t.text_3}; background: transparent; padding: 0 2px;"
                    )
                    lo.addWidget(plus)
            lo.addStretch()
            edit = QLabel("Modifier")
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
