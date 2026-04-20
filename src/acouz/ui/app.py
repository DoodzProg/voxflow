"""
AcouZ - Open-source AI voice dictation
Copyright (c) 2025-2026 DoodzProg
Licensed under the MIT License

Main application window, floating voice overlay and entry point.

Architecture
------------
- :class:`VoiceOverlay`  — frameless floating widget shown during dictation.
- :class:`AcouZApp`      — top-level :class:`~PySide6.QtWidgets.QMainWindow`;
  owns navigation, theming, dictation lifecycle and history management.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import sounddevice as sd

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QPushButton, QLabel, QStackedWidget,
    QFrame, QSystemTrayIcon, QMenu, QMessageBox,
)
from PySide6.QtGui import QColor, QPainter, QPen, QIcon, QPixmap, QCursor
from PySide6.QtCore import Qt, QTimer, Signal, QByteArray, QEvent
from PySide6.QtSvgWidgets import QSvgWidget

from acouz.utils.config import ConfigManager
from acouz.core.engine import DictationEngine
from acouz.core.hotkey import HotkeyListener
from acouz.platform import (
    apply_dwm_rounded_corners,
    capture_selected_text,
    send_paste,
    get_foreground_window,
)

import acouz.ui.styles as S
from acouz.ui.styles import ICONS, Theme, DARK, LOGO_SVG
from acouz.ui.components import (
    set_theme, _t, make_svg, reload_svg,
    PillBadge, NavButton, TitleBar,
)
from acouz.ui.pages import HomePage, GeneralPage, ApiPage, AudioPage, AboutPage
from acouz.utils.i18n import tr
from PySide6.QtSvg import QSvgRenderer

def _make_app_icon() -> QIcon:
    """Render ``LOGO_SVG`` into a :class:`~PySide6.QtGui.QIcon` at all standard
    Windows icon sizes (16 → 256 px).

    Returns:
        A multi-resolution :class:`~PySide6.QtGui.QIcon` suitable for the
        window title bar, taskbar and system-tray contexts.
    """
    renderer = QSvgRenderer(QByteArray(LOGO_SVG.encode()))
    icon = QIcon()
    from PySide6.QtGui import QImage  # noqa: PLC0415
    for size in (16, 24, 32, 48, 64, 128, 256):
        img = QImage(size, size, QImage.Format_ARGB32)
        img.fill(0)
        p = QPainter(img)
        renderer.render(p)
        p.end()
        icon.addPixmap(QPixmap.fromImage(img))
    return icon


# Add the "copy" icon that is not in the default ICONS dictionary
ICONS["copy"] = (
    '<rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>'
    '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>'
)


# ─────────────────────────────────────────────────────────────
#  VOICE OVERLAY — BARS ANIMATION SUBWIDGET
# ─────────────────────────────────────────────────────────────

class _OverlayBars(QWidget):
    """Compact animated bar-chart that visualises the microphone RMS level.

    Intended as a child widget of :class:`VoiceOverlay`.  The accent colour
    is read from the live theme at paint time so it updates automatically.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.level: float = 0.0
        self.setFixedSize(48, 30)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event) -> None:  # type: ignore[override]
        """Draw five rounded bars whose heights scale with :attr:`level`."""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(_t().accent))

        bar_w, gap, num = 4, 3, 5
        total_w = num * bar_w + (num - 1) * gap
        sx = (self.width() - total_w) // 2
        cy = self.height() // 2
        base_h, max_h = 4, 20

        for i in range(num):
            dist = abs(i - num // 2)
            h = base_h + self.level * max_h * (1.0 - dist * 0.3)
            x = sx + i * (bar_w + gap)
            y = cy - h / 2
            p.drawRoundedRect(int(x), int(y), bar_w, int(h), 2, 2)

        p.end()


# ─────────────────────────────────────────────────────────────
#  VOICE OVERLAY
# ─────────────────────────────────────────────────────────────

class VoiceOverlay(QWidget):
    """Themed floating bubble shown at the bottom of the screen during dictation.

    Displays a status label, an animated bar-chart VU-meter and two action
    buttons: cancel (✕, discards audio) and confirm (✓, processes audio).

    Signals:
        cancel_requested:  Emitted when the user clicks ✕.
        confirm_requested: Emitted when the user clicks ✓.

    Args:
        parent: Optional parent widget (normally ``None`` for a top-level window).
    """

    cancel_requested = Signal()
    confirm_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Compact pill size — slightly smaller than the initial 320×58
        self.setFixedSize(270, 50)

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick)
        self._anim_timer.setInterval(1000 // 30)

        self._build()

    # ------------------------------------------------------------------

    def _build(self) -> None:
        """Construct the overlay layout: [✕] [label] [bars] ─── [✓]."""
        t = _t()
        lo = QHBoxLayout(self)
        lo.setContentsMargins(10, 0, 10, 0)
        lo.setSpacing(8)

        # ── Cancel button — LEFT of the label (discards audio) ──────
        self._btn_cancel = QPushButton()
        self._btn_cancel.setFixedSize(30, 30)
        self._btn_cancel.setCursor(Qt.PointingHandCursor)
        self._btn_cancel.setFocusPolicy(Qt.NoFocus)
        _cl = QHBoxLayout(self._btn_cancel)
        _cl.setContentsMargins(0, 0, 0, 0)
        self._cancel_svg = make_svg("x_mark", 12, t.text_2)
        _cl.addWidget(self._cancel_svg, 0, Qt.AlignCenter)
        self._btn_cancel.clicked.connect(self.cancel_requested)
        lo.addWidget(self._btn_cancel, 0, Qt.AlignVCenter)

        # ── Status label ─────────────────────────────────────────────
        self._lbl = QLabel(tr("overlay.dictation"))
        lo.addWidget(self._lbl)

        # ── Animated bars ────────────────────────────────────────────
        self._bars = _OverlayBars(self)
        lo.addWidget(self._bars)
        lo.addStretch()

        # ── Confirm button — RIGHT (sends audio for processing) ──────
        self._btn_confirm = QPushButton()
        self._btn_confirm.setFixedSize(30, 30)
        self._btn_confirm.setCursor(Qt.PointingHandCursor)
        self._btn_confirm.setFocusPolicy(Qt.NoFocus)
        _cf = QHBoxLayout(self._btn_confirm)
        _cf.setContentsMargins(0, 0, 0, 0)
        self._confirm_svg = make_svg("check", 12, t.accent)
        _cf.addWidget(self._confirm_svg, 0, Qt.AlignCenter)
        self._btn_confirm.clicked.connect(self.confirm_requested)
        lo.addWidget(self._btn_confirm, 0, Qt.AlignVCenter)

        self._apply_style(t)

    def _apply_style(self, t: Theme) -> None:
        """Apply theme-aware colours to all child widgets.

        Args:
            t: Active :class:`~acouz.ui.styles.Theme`.
        """
        self._lbl.setStyleSheet(
            f"color: {t.text_1}; background: transparent; "
            f"font-size: 13px; font-family: 'Segoe UI Variable', 'Segoe UI';"
        )
        # Cancel: neutral gray, danger colour on hover
        dr = t.danger.lstrip("#")
        self._btn_cancel.setStyleSheet(
            f"QPushButton {{ background: {t.bg_hover}; border: none; "
            f"border-radius: 15px; }} "
            f"QPushButton:hover {{ background: #22{dr}; }}"
        )
        reload_svg(self._cancel_svg, "x_mark", t.text_2)
        # Confirm: subtle accent fill, brighter on hover
        rgb = t.accent.lstrip("#")
        self._btn_confirm.setStyleSheet(
            f"QPushButton {{ background: #22{rgb}; border: none; "
            f"border-radius: 15px; }} "
            f"QPushButton:hover {{ background: #44{rgb}; }}"
        )
        reload_svg(self._confirm_svg, "check", t.accent)

    def retheme(self, t: Theme) -> None:
        """Update colours and repaint when the application theme changes.

        Args:
            t: New active theme.
        """
        self._apply_style(t)
        self.update()

    # ------------------------------------------------------------------

    def set_text(self, text: str) -> None:
        """Update the status label.

        Args:
            text: E.g. ``"Dictée…"`` or ``"Instructions…"``.
        """
        self._lbl.setText(text)

    def set_level(self, rms: float) -> None:
        """Forward a new RMS level to the bar visualiser.

        Args:
            rms: Normalised amplitude ``[0.0, 1.0]``.
        """
        import math  # noqa: PLC0415
        if math.isnan(rms) or math.isinf(rms):
            rms = 0.0
        self._bars._target = min(rms * 15.0, 1.0)

    def _tick(self) -> None:
        """Smooth the bar level with a low-pass filter and repaint."""
        target = getattr(self._bars, "_target", 0.0)
        self._bars.level = self._bars.level * 0.6 + target * 0.4
        self._bars.update()

    def showEvent(self, event) -> None:  # type: ignore[override]
        """Start the animation timer."""
        self._anim_timer.start()
        super().showEvent(event)

    def hideEvent(self, event) -> None:  # type: ignore[override]
        """Stop the timer and reset visualiser state."""
        self._anim_timer.stop()
        self._bars.level = 0.0
        super().hideEvent(event)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        """Draw the themed rounded-rect background behind the child widgets."""
        t = _t()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(t.border), 1)
        p.setPen(pen)
        p.setBrush(QColor(t.bg_card))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 29, 29)
        p.end()


# ─────────────────────────────────────────────────────────────
#  MAIN WINDOW
# ─────────────────────────────────────────────────────────────

class AcouZApp(QMainWindow):
    """Top-level application window; owns navigation and live theme switching.

    The window stays alive in the system tray when the user closes it.
    Dictation sessions are driven by :class:`~acouz.core.hotkey.HotkeyListener`
    and :class:`~acouz.core.engine.DictationEngine`.

    Args:
        parent: Optional parent widget.
    """

    # Resize border thickness (pixels) used in nativeEvent hit-testing
    _BORDER: int = 12
    # Corner-radius of the rounded window background
    _RADIUS: int = 12

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AcouZ")
        self.setWindowIcon(_make_app_icon())
        self.resize(860, 580)
        self.setMinimumSize(720, 480)

        # ── Frameless + translucent so we can draw rounded corners ──
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._is_dictating: bool = False
        self._target_wid: int = 0      # XID of the window to paste into (Linux)
        self._linux_resize: bool = sys.platform != "win32"
        self._resize_cursor_active: bool = False
        self.record_start_time: float = 0.0
        self.history_data: list[dict] = []
        self.history_file: str = os.path.join(
            os.path.dirname(__file__), "../../history.json"
        )

        self._build_tray()
        self._build_layout()
        self._wire_backend()

        self.apply_theme()
        self.load_history()
        self.refresh_home_shortcuts()
        self.home_page.btn_clear.clicked.connect(self.clear_history)

        # Apply Windows 11 DWM rounded corners once the native HWND exists.
        # A zero-delay timer ensures this runs after the first paint event,
        # which is when the handle is guaranteed to be created.
        QTimer.singleShot(0, self._apply_dwm_rounded_corners)

        # Install an application-level event filter on Linux to intercept
        # mouse events from all child widgets for border-resize detection.
        if self._linux_resize:
            QApplication.instance().installEventFilter(self)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _apply_dwm_rounded_corners(self) -> None:
        if sys.platform == "win32":
            apply_dwm_rounded_corners(int(self.winId()))
        else:
            self._apply_linux_mask()

    def _apply_linux_mask(self) -> None:
        """Clip the window to a rounded rectangle via a QBitmap mask.

        Called once after first paint and again on every resize event.
        Works without a compositor (pure X11/XCB, no Wayland needed).
        """
        from PySide6.QtGui import QBitmap, QRegion  # noqa: PLC0415
        from PySide6.QtCore import Qt               # noqa: PLC0415
        bmp = QBitmap(self.size())
        bmp.fill(Qt.color0)
        p = QPainter(bmp)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(Qt.color1)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(
            self.rect().adjusted(0, 0, -1, -1),
            self._RADIUS, self._RADIUS,
        )
        p.end()
        self.setMask(QRegion(bmp))

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """Re-apply rounded mask on Linux when the window is resized."""
        if sys.platform != "win32":
            self._apply_linux_mask()
        super().resizeEvent(event)

    # ------------------------------------------------------------------
    # Linux border resize — event filter + QWindow.startSystemResize
    # ------------------------------------------------------------------

    def _get_resize_edges(self, local_pos) -> "Qt.Edges":
        """Return the ``Qt.Edges`` bitmask for a cursor position near a border.

        Args:
            local_pos: Cursor position in window-local coordinates.

        Returns:
            ``Qt.Edges`` flags for the active resize direction(s), or an empty
            flags value when the cursor is not within ``_BORDER`` pixels of
            any window edge.
        """
        x, y = local_pos.x(), local_pos.y()
        w, h = self.width(), self.height()
        b = self._BORDER
        edges = Qt.Edges(0)
        if 0 <= x < b:        edges |= Qt.Edge.LeftEdge
        if w - b <= x <= w:   edges |= Qt.Edge.RightEdge
        if 0 <= y < b:        edges |= Qt.Edge.TopEdge
        if h - b <= y <= h:   edges |= Qt.Edge.BottomEdge
        return edges

    def _update_resize_cursor(self) -> None:
        """Set or restore the window cursor based on border proximity.

        Uses ``QApplication.setOverrideCursor`` / ``changeOverrideCursor`` so
        the cursor change applies even when the pointer is over a child widget
        that has its own cursor.
        """
        local = self.mapFromGlobal(QCursor.pos())
        edges = self._get_resize_edges(local)

        left   = bool(edges & Qt.Edge.LeftEdge)
        right  = bool(edges & Qt.Edge.RightEdge)
        top    = bool(edges & Qt.Edge.TopEdge)
        bottom = bool(edges & Qt.Edge.BottomEdge)

        if (left and top) or (right and bottom):
            shape = Qt.CursorShape.SizeFDiagCursor
        elif (right and top) or (left and bottom):
            shape = Qt.CursorShape.SizeBDiagCursor
        elif left or right:
            shape = Qt.CursorShape.SizeHorCursor
        elif top or bottom:
            shape = Qt.CursorShape.SizeVerCursor
        else:
            shape = None

        if shape is not None:
            cursor = QCursor(shape)
            if not self._resize_cursor_active:
                QApplication.setOverrideCursor(cursor)
                self._resize_cursor_active = True
            else:
                QApplication.changeOverrideCursor(cursor)
        else:
            self._clear_resize_cursor()

    def _clear_resize_cursor(self) -> None:
        """Restore the default cursor if a resize-direction override is active."""
        if self._resize_cursor_active:
            QApplication.restoreOverrideCursor()
            self._resize_cursor_active = False

    def eventFilter(self, obj: object, event: object) -> bool:  # type: ignore[override]
        """Intercept mouse events to provide border resize on Linux.

        Installed on ``QApplication`` (not just ``self``) so that events from
        all child widgets are visible.  Ignored on Windows — native
        ``WM_NCHITTEST`` handles resize there.

        Strategy:
          - ``MouseMove``        → update the cursor shape near borders.
          - ``MouseButtonPress`` → call ``QWindow.startSystemResize()`` on the
                                   underlying ``QWindow`` handle, which sends
                                   ``_NET_WM_MOVERESIZE`` on X11/XWayland and
                                   the Wayland ``xdg_toplevel.resize`` request
                                   on Wayland-native compositors.
          - ``Leave``            → restore the default cursor.

        Args:
            obj:   Object that received the event (any widget in the app).
            event: The event to inspect.

        Returns:
            ``True`` to consume the event (when handing off to system resize),
            ``False`` to let it propagate normally.
        """
        if not self._linux_resize:
            return False

        etype = event.type()  # type: ignore[attr-defined]

        if etype == QEvent.Type.MouseMove:
            self._update_resize_cursor()

        elif etype == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:  # type: ignore[attr-defined]
                local = self.mapFromGlobal(QCursor.pos())
                edges = self._get_resize_edges(local)
                if edges:
                    handle = self.windowHandle()
                    if handle and handle.startSystemResize(edges):
                        self._clear_resize_cursor()
                        return True  # Consume — don't let TitleBar also start a drag.

        elif etype == QEvent.Type.Leave:
            self._clear_resize_cursor()

        return False

    def _build_tray(self) -> None:
        """Create and show the system tray icon with its context menu."""
        self.tray_icon = QSystemTrayIcon(self)
        # Reuse the same multi-resolution icon as the main window.
        self.tray_icon.setIcon(_make_app_icon())

        tray_menu = QMenu()
        show_action = tray_menu.addAction("Ouvrir les paramètres")
        show_action.triggered.connect(self.show_normal)
        quit_action = tray_menu.addAction("Quitter AcouZ")
        quit_action.triggered.connect(self.quit_app)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("AcouZ")
        self.tray_icon.activated.connect(self._on_tray_click)
        self.tray_icon.show()

    def _build_layout(self) -> None:
        """Assemble the titlebar + sidebar + stacked-page root layout."""
        t = _t()

        # ── Rounded container acts as the visible window background ──
        self._root_w = _RoundedContainer(self)
        self.setCentralWidget(self._root_w)
        outer = QVBoxLayout(self._root_w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Custom title bar (drag + window controls)
        self._titlebar = TitleBar(self)
        outer.addWidget(self._titlebar)

        # Content row (sidebar + pages)
        content_w = QWidget()
        content_w.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(content_w)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(0)
        outer.addWidget(content_w, 1)

        # ── Sidebar ──────────────────────────────────────────────────
        self._sidebar = QFrame()
        self._sidebar.setFixedWidth(220)
        self._sidebar.setStyleSheet(S.sidebar_qss(t))
        sb = QVBoxLayout(self._sidebar)
        sb.setContentsMargins(10, 22, 10, 16)
        sb.setSpacing(2)

        # Logo row
        logo_r = QHBoxLayout()
        logo_r.setSpacing(8)
        self._logo_icon = make_svg("mic", 18, t.accent_light)
        logo_r.addWidget(self._logo_icon)
        self._logo_lbl = QLabel("AcouZ")
        self._logo_lbl.setStyleSheet(
            f"color: {t.text_1}; font-size: 17px; font-weight: 700; "
            f"font-family: 'Segoe UI'; background: transparent;"
        )
        logo_r.addWidget(self._logo_lbl)
        self._alpha_badge = PillBadge("v1.0.2", t.accent_purple)
        logo_r.addWidget(self._alpha_badge)
        logo_r.addStretch()
        sb.addLayout(logo_r)
        sb.addSpacing(20)

        # Nav buttons — labels are translated at build time and updated by
        # retranslate_all() when the user changes the interface language.
        nav_defs: list[tuple[str, str]] = [
            ("home",     tr("nav.home")),
            ("settings", tr("nav.settings")),
            ("key",      tr("nav.api")),
            ("volume",   tr("nav.audio")),
            ("info",     tr("nav.about")),
        ]
        # Store the i18n keys alongside the buttons for retranslation.
        self._nav_keys = ["nav.home", "nav.settings", "nav.api", "nav.audio", "nav.about"]
        self._nav_btns: list[NavButton] = []
        for ik, lbl in nav_defs:
            btn = NavButton(ik, lbl)
            btn.clicked.connect(lambda _, i=len(self._nav_btns): self._go(i))
            sb.addWidget(btn)
            self._nav_btns.append(btn)
        sb.addStretch()

        # Quit button
        self._quit_btn = QPushButton(tr("sidebar.quit"))
        self._quit_btn.setFixedHeight(36)
        self._quit_btn.setCursor(Qt.PointingHandCursor)
        self._quit_btn.clicked.connect(self.quit_app)
        sb.addWidget(self._quit_btn)
        sb.addSpacing(6)

        # Status bar
        self._status_frame = QFrame()
        self._status_frame.setStyleSheet(S.status_bar_qss(t))
        str_ = QHBoxLayout(self._status_frame)
        str_.setContentsMargins(12, 8, 12, 8)
        str_.setSpacing(8)
        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet(
            f"color: {t.accent_light}; font-size: 9px; background: transparent;"
        )
        self.status_label = QLabel(tr("sidebar.status.init"))
        self.status_label.setStyleSheet(
            f"color: {t.text_2}; font-size: 11px; "
            f"font-family: 'Segoe UI'; background: transparent;"
        )
        str_.addWidget(self._status_dot)
        str_.addWidget(self.status_label)
        str_.addStretch()
        sb.addWidget(self._status_frame)

        # ── Stacked pages ────────────────────────────────────────────
        self.home_page = HomePage()
        self.general_page = GeneralPage()
        self.api_page = ApiPage()
        self.audio_page = AudioPage()
        self.about_page = AboutPage()

        self._pages = [
            self.home_page, self.general_page, self.api_page,
            self.audio_page, self.about_page,
        ]

        self.pages = QStackedWidget()
        self.pages.setStyleSheet(S.pages_qss(t))
        for page in self._pages:
            self.pages.addWidget(page)

        hl.addWidget(self._sidebar)
        hl.addWidget(self.pages, 1)
        self._go(0)

        # Connect language-change signal so the entire UI reacts instantly.
        self.general_page.language_changed.connect(self.retranslate_all)

    def _wire_backend(self) -> None:
        """Instantiate and connect the dictation engine and hotkey listener."""
        self.engine = DictationEngine(self)
        self.hotkey_listener = HotkeyListener(self)

        self.voice_overlay = VoiceOverlay()
        self.engine.audio_level_changed.connect(self.voice_overlay.set_level)
        self.voice_overlay.cancel_requested.connect(self.cancel_dictation)
        self.voice_overlay.confirm_requested.connect(self._on_hotkey_released)

        self.engine.status_changed.connect(self.update_status)
        self.engine.text_ready.connect(self.on_text_ready)
        self.engine.error_occurred.connect(
            lambda msg: self.update_status(f"{tr('engine.error')}: {msg}")
        )

        self.hotkey_listener.hotkey_dictate_pressed.connect(self.start_dictation)
        self.hotkey_listener.hotkey_dictate_released.connect(self._on_hotkey_released)
        self.hotkey_listener.hotkey_context_pressed.connect(
            self.start_context_dictation
        )
        self.hotkey_listener.hotkey_context_released.connect(self._on_hotkey_released)
        self.hotkey_listener.start()
        self.update_status(tr("engine.ready"))

    # ------------------------------------------------------------------
    # Theme switching
    # ------------------------------------------------------------------

    def apply_theme(self) -> None:
        """Apply the single dark theme to the entire application."""
        set_theme(True)
        t = _t()

        app = QApplication.instance()
        app.setPalette(S.get_palette(True))
        app.setStyleSheet(S.get_qss(True))

        self._root_w.update()
        self._titlebar.retheme(t)

        if hasattr(self, "voice_overlay"):
            self.voice_overlay.retheme(t)

        self._sidebar.setStyleSheet(S.sidebar_qss(t))
        reload_svg(self._logo_icon, "mic", t.accent_light)
        self._logo_lbl.setStyleSheet(
            f"color: {t.text_1}; font-size: 17px; font-weight: 700; "
            f"font-family: 'Segoe UI'; background: transparent;"
        )
        self._alpha_badge.setStyleSheet(S.pill_badge_qss(t.accent_purple))

        for btn in self._nav_btns:
            btn.retheme()

        self._quit_btn.setStyleSheet(
            f"QPushButton {{ text-align: left; padding-left: 14px; "
            f"background: transparent; color: {t.text_2}; border-radius: 6px; "
            f"font-size: 13px; font-weight: 500; font-family: 'Segoe UI'; }} "
            f"QPushButton:hover {{ background: rgba(239,68,68,0.15); "
            f"color: {t.danger}; }}"
        )

        self._status_frame.setStyleSheet(S.status_bar_qss(t))
        self._status_dot.setStyleSheet(
            f"color: {t.accent_light}; font-size: 9px; background: transparent;"
        )
        self.status_label.setStyleSheet(
            f"color: {t.text_2}; font-size: 11px; "
            f"font-family: 'Segoe UI'; background: transparent;"
        )

        self.pages.setStyleSheet(S.pages_qss(t))

        for page in self._pages:
            page.retheme(t)

        self.refresh_dashboard()
        self.refresh_home_shortcuts()

    # ------------------------------------------------------------------
    # Language switching
    # ------------------------------------------------------------------

    def retranslate_all(self, _lang: str = "") -> None:
        """Update every user-visible string to the current UI language.

        Called automatically when :attr:`~acouz.ui.pages.general.GeneralPage.language_changed`
        is emitted.  Also safe to call manually at any time.

        Args:
            _lang: Ignored — language is read from :class:`~acouz.utils.config.ConfigManager`
                   by each :func:`~acouz.utils.i18n.tr` call.
        """
        # Sidebar static text
        self._quit_btn.setText(tr("sidebar.quit"))

        # Navigation button labels
        for btn, key in zip(self._nav_btns, self._nav_keys):
            btn.set_label(tr(key))

        # All pages
        for page in self._pages:
            page.retranslate()

        # Dynamic home page content uses tr() inside rebuild helpers.
        self.refresh_dashboard()
        self.refresh_home_shortcuts()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _go(self, idx: int) -> None:
        """Navigate to the page at the given zero-based index.

        Args:
            idx: Target page index (0 = home, 1 = settings, …).
        """
        self.pages.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_btns):
            btn.set_active(i == idx)

    # ------------------------------------------------------------------
    # Dictation lifecycle
    # ------------------------------------------------------------------

    def start_dictation(self) -> None:
        """Begin a simple (no-context) dictation session.

        Captures the foreground window XID before the overlay appears so that
        ``send_paste`` can target the correct window on Linux even after the
        overlay steals focus.
        """
        if self._is_dictating:
            return
        self._target_wid = get_foreground_window()
        self._is_dictating = True
        self.record_start_time = time.time()
        self.play_beep(start=True)
        self.engine.set_context("")
        self.engine.start_recording()
        self._show_overlay(tr("overlay.dictation"))

    def start_context_dictation(self, previous_hwnd: int) -> None:
        """Begin a context-aware dictation session.

        Captures the currently selected text from the foreground application
        before starting the recording, using UIAutomation (Plan A) and a
        raw SendInput Ctrl+C fallback for Chromium-based apps (Plan B).

        Args:
            previous_hwnd: HWND of the window that was active before the
                hotkey was pressed.
        """
        if self._is_dictating:
            return
        self._target_wid = previous_hwnd
        self._is_dictating = True
        self.record_start_time = time.time()
        self.play_beep(start=True)

        clipboard = QApplication.clipboard()
        from PySide6.QtCore import QMimeData  # noqa: PLC0415
        original_mime = clipboard.mimeData()
        backup_mime = QMimeData()
        for fmt in original_mime.formats():
            backup_mime.setData(fmt, original_mime.data(fmt))

        def _extract() -> None:
            context_text = capture_selected_text(clipboard)
            clipboard.setMimeData(backup_mime)
            context_text = context_text.strip()
            self.engine.set_context(context_text)
            if self._is_dictating:
                self.engine.start_recording()
                self._show_overlay(tr("overlay.context"))

        QTimer.singleShot(50, _extract)

    def cancel_dictation(self) -> None:
        """Discard the current recording without transcription.

        Connected to :attr:`~VoiceOverlay.cancel_requested`.
        """
        if not self._is_dictating:
            return
        self._is_dictating = False
        self.voice_overlay.hide()
        self.engine.cancel_recording()
        self.update_status("Dictée annulée")

    def _on_hotkey_released(self) -> None:
        """Handle hotkey release or confirm button: stop recording and process."""
        if self._is_dictating:
            self.play_beep(start=False)
        self._is_dictating = False
        self.voice_overlay.hide()
        self.engine.stop_recording_and_process()

    # ------------------------------------------------------------------
    # Audio feedback
    # ------------------------------------------------------------------

    def play_beep(self, start: bool) -> None:
        """Play a soft confirmation chime in a daemon thread.

        Uses ``sounddevice`` to synthesise and immediately play a short
        piano-style tone without blocking the UI thread.

        Args:
            start: ``True`` to play the start chime (two-note arpeggio),
                   ``False`` for the stop chime (single descending note).
        """
        if ConfigManager.get("CONFIRMATION_SOUND", "true") != "true":
            return

        import threading  # noqa: PLC0415

        def _chime(freq: float, duration: float, volume: float,
                   sr: int = 44100) -> np.ndarray:
            t = np.linspace(0, duration, int(sr * duration), endpoint=False)
            wave = np.sin(2 * np.pi * freq * (1.0 - 0.03 * t / duration) * t)
            env = np.exp(-6.0 * t / duration)
            fi = int(sr * 0.004)
            env[:fi] *= np.linspace(0, 1, fi)
            return (wave * env * volume).astype(np.float32)

        def _play(audio: np.ndarray, sr: int = 44100) -> None:
            sd.play(audio, sr)
            sd.wait()

        if start:
            sr = 44100
            n1 = _chime(880.0, 0.22, 0.20, sr)
            n2 = _chime(1320.0, 0.25, 0.15, sr)
            offset = int(sr * 0.12)
            total = max(len(n1), offset + len(n2))
            mixed = np.zeros(total, dtype=np.float32)
            mixed[: len(n1)] += n1
            mixed[offset: offset + len(n2)] += n2
            peak = np.max(np.abs(mixed))
            if peak > 1.0:
                mixed /= peak
            threading.Thread(target=_play, args=(mixed, sr), daemon=True).start()
        else:
            threading.Thread(
                target=_play, args=(_chime(660.0, 0.45, 0.20),), daemon=True
            ).start()

    # ------------------------------------------------------------------
    # Text injection & history
    # ------------------------------------------------------------------

    def on_text_ready(self, text: str) -> None:
        """Called when the engine has finished processing; inject text and save history.

        Saves the current clipboard, sets the dictated text, fires Ctrl+V via
        the ``keyboard`` library, then restores the original clipboard contents
        after a 250 ms delay.

        Args:
            text: Final corrected transcription string.
        """
        duration = (
            time.time() - self.record_start_time
            if self.record_start_time > 0
            else 0.0
        )
        entry = {
            "text": text,
            "words": len(text.split()),
            "duration": duration,
            "timestamp": time.time(),
        }
        self.history_data.append(entry)
        self.save_history()
        self.refresh_dashboard()

        from PySide6.QtCore import QMimeData  # noqa: PLC0415
        clipboard = QApplication.clipboard()
        original_mime = clipboard.mimeData()
        backup_mime = QMimeData()
        for fmt in original_mime.formats():
            backup_mime.setData(fmt, original_mime.data(fmt))

        clipboard.setText(text)

        def _paste_and_restore() -> None:
            send_paste(self._target_wid)
            QTimer.singleShot(250, lambda: clipboard.setMimeData(backup_mime))

        QTimer.singleShot(50, _paste_and_restore)

    def load_history(self) -> None:
        """Load dictation history from the JSON persistence file on startup."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, encoding="utf-8") as f:
                    self.history_data = json.load(f)
        except Exception:
            self.history_data = []
        self.refresh_dashboard()

    def save_history(self) -> None:
        """Persist the in-memory history list to the JSON file.

        Raises:
            IOError: If the file cannot be written (caught and logged internally).
        """
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"[History] Save error: {exc}")

    def clear_history(self) -> None:
        """Prompt the user for confirmation, then wipe history and reset stats."""
        box = QMessageBox(self)
        box.setWindowTitle("Confirmer la réinitialisation")
        box.setText("Attention !")
        box.setInformativeText(
            "Vous allez perdre tout l'historique de vos transcriptions locales "
            "ainsi que toutes les statistiques associées.\n\nContinuer ?"
        )
        box.setIcon(QMessageBox.Warning)
        btn_yes = box.addButton("Oui, tout effacer", QMessageBox.AcceptRole)
        box.addButton("Annuler", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() == btn_yes:
            self.history_data = []
            self.save_history()
            self.refresh_dashboard()

    def refresh_dashboard(self) -> None:
        """Recalculate statistics and redraw the history list on the home page."""
        if not hasattr(self, "home_page"):
            return

        total_words = sum(e["words"] for e in self.history_data)
        total_sec = sum(e["duration"] for e in self.history_data)
        sessions = len(self.history_data)
        total_min = total_sec / 60.0
        wpm = int(total_words / total_min) if total_min > 0 else 0

        self.home_page.stat_words.set_value(f"{total_words} {tr('home.stat.words.unit')}")
        self.home_page.stat_time.set_value(
            f"{int(total_sec)} sec" if total_min < 1 else f"{int(total_min)} min"
        )
        self.home_page.stat_wpm.set_value(f"{wpm} {tr('home.stat.wpm.unit')}")
        self.home_page.stat_sessions.set_value(str(sessions))

        layout = self.home_page.history_layout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        t = _t()
        recent = list(reversed(self.history_data))[:10]
        if not recent:
            lbl = QLabel(tr("home.empty"))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                f"color: {t.text_3}; font-size: 13px; "
                f"font-family: 'Segoe UI'; padding: 30px;"
            )
            layout.addWidget(lbl)
            return

        from PySide6.QtWidgets import QFrame  # noqa: PLC0415
        for entry in recent:
            f = QFrame()
            f.setStyleSheet(S.card_qss(t))
            lv = QVBoxLayout(f)
            lv.setContentsMargins(18, 14, 18, 14)
            row = QHBoxLayout()
            row.setSpacing(12)

            lbl = QLabel(f"« {entry['text']} »")
            lbl.setWordWrap(True)
            lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            lbl.setCursor(Qt.IBeamCursor)
            lbl.setStyleSheet(
                f"color: {t.text_1}; font-size: 13px; font-style: italic; "
                f"background: transparent; selection-background-color: {t.accent};"
            )

            btn_copy = QPushButton()
            btn_copy.setFixedSize(28, 28)
            btn_copy.setCursor(Qt.PointingHandCursor)
            btn_copy.setStyleSheet(
                "QPushButton { background: transparent; border: none; border-radius: 4px; } "
                "QPushButton:hover { background: rgba(150,150,150,0.15); }"
            )
            ic_copy = make_svg("copy", 14, t.text_3)
            from PySide6.QtWidgets import QHBoxLayout as _HBox  # noqa: PLC0415
            ic_lo = _HBox(btn_copy)
            ic_lo.setContentsMargins(0, 0, 0, 0)
            ic_lo.addWidget(ic_copy, 0, Qt.AlignCenter)
            btn_copy.clicked.connect(
                lambda _=False, txt=entry["text"]:
                QApplication.clipboard().setText(txt)
            )

            row.addWidget(lbl, 1)
            row.addWidget(btn_copy, 0, Qt.AlignTop)
            lv.addLayout(row)
            layout.addWidget(f)

    def refresh_home_shortcuts(self) -> None:
        """Rebuild the shortcut cards on the home page from current config."""
        if not hasattr(self, "home_page"):
            return

        lo = self.home_page.shortcuts_layout
        while lo.count():
            item = lo.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()
                item.layout().deleteLater()

        t = _t()
        hk_dict = ConfigManager.get("HOTKEY_DICTATE", "right ctrl+right shift")
        mod_dict = ConfigManager.get("HOTKEY_DICTATE_MODE", "hold")
        self._add_shortcut_card(tr("home.shortcut.dictate"), hk_dict, mod_dict, "mic", t)

        hk_ctx = ConfigManager.get("HOTKEY_CONTEXT", "right alt+right shift")
        mod_ctx = ConfigManager.get("HOTKEY_CONTEXT_MODE", "hold")
        self._add_shortcut_card(
            tr("home.shortcut.context"), hk_ctx, mod_ctx, "zap", t
        )

    def _add_shortcut_card(
        self, title: str, hotkey_str: str, mode: str, icon: str, t: Theme
    ) -> None:
        """Append a single shortcut summary card to the home page shortcuts area.

        Args:
            title:      Card heading text.
            hotkey_str: Raw hotkey string (e.g. ``"right ctrl+right shift"``).
            mode:       Trigger mode — ``"hold"`` or ``"toggle"``.
            icon:       Icon key from :data:`~acouz.ui.styles.ICONS`.
            t:          Active theme.
        """
        from PySide6.QtWidgets import QFrame  # noqa: PLC0415
        sc = QFrame()
        sc.setStyleSheet(S.shortcut_card_qss(t))
        sc_r = QHBoxLayout(sc)
        sc_r.setContentsMargins(22, 18, 22, 18)
        sc_r.setSpacing(16)
        sc_r.addWidget(make_svg(icon, 26, t.accent_light))

        tc = QVBoxLayout()
        tc.setSpacing(2)
        t1 = QLabel(title)
        t1.setStyleSheet(
            f"color: {t.text_1}; font-size: 13px; font-weight: 600; "
            f"font-family: 'Segoe UI'; background: transparent;"
        )
        action = (
            tr("home.shortcut.hold")
            if mode == "hold"
            else tr("home.shortcut.toggle")
        )
        t2 = QLabel(action)
        t2.setStyleSheet(
            f"color: {t.text_2}; font-size: 12px; "
            f"font-family: 'Segoe UI'; background: transparent;"
        )
        tc.addWidget(t1)
        tc.addWidget(t2)
        sc_r.addLayout(tc)
        sc_r.addStretch()

        keys = [k.strip().title() for k in hotkey_str.split("+")]
        hk_lo = QHBoxLayout()
        hk_lo.setSpacing(8)
        for i, k in enumerate(keys):
            chip = QLabel(k)
            chip.setStyleSheet(S.shortcut_chip_style(t))
            hk_lo.addWidget(chip)
            if i < len(keys) - 1:
                sep = QLabel("+")
                sep.setStyleSheet(
                    f"color: {t.text_3}; background: transparent; padding: 0 2px;"
                )
                hk_lo.addWidget(sep)
        sc_r.addLayout(hk_lo)
        self.home_page.shortcuts_layout.addWidget(sc)

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------

    def update_status(self, text: str) -> None:
        """Update the sidebar status label text.

        Args:
            text: Status message to display (e.g. ``"Enregistrement…"``).
        """
        self.status_label.setText(text)

    # ------------------------------------------------------------------
    # Overlay helpers
    # ------------------------------------------------------------------

    def _show_overlay(self, text: str) -> None:
        """Position and show the voice overlay at the bottom-centre of the screen.

        Respects the ``SHOW_OVERLAY`` config key; when the user has disabled
        the bubble this method is a no-op.

        Args:
            text: Initial label text for the overlay bubble.
        """
        if ConfigManager.get("SHOW_OVERLAY", "true") != "true":
            return
        self.voice_overlay.set_text(text)
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.voice_overlay.width()) // 2
        y = screen.height() - self.voice_overlay.height() - 56
        self.voice_overlay.move(x, y)
        self.voice_overlay.show()

    # ------------------------------------------------------------------
    # Window / tray management
    # ------------------------------------------------------------------

    def _on_tray_click(
        self, reason: QSystemTrayIcon.ActivationReason
    ) -> None:
        """Restore the window on tray double-click.

        Args:
            reason: PySide6 activation reason enum value.
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_normal()

    def show_normal(self) -> None:
        """Restore and focus the main window from the system tray."""
        self.show()
        self.activateWindow()

    def quit_app(self) -> None:
        """Stop all background threads and quit the application."""
        if hasattr(self, "hotkey_listener"):
            self.hotkey_listener.stop()
        if hasattr(self, "engine") and self.engine.isRunning():
            self.engine.quit()
            self.engine.wait()
        QApplication.instance().quit()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Minimise to the system tray instead of quitting on window close."""
        event.ignore()
        self.hide()

    def nativeEvent(self, eventType: bytes, message: object):  # type: ignore[override]
        """Intercept WM_NCHITTEST to provide native resize hit zones.

        Returns the appropriate ``HTxxx`` code for each of the 8 resize
        directions when the cursor is within :attr:`_BORDER` pixels of the
        window edge, giving the OS full control over cursor shape and resize
        behaviour (Aero-Snap compatible).

        Args:
            eventType: Platform-specific event type bytes.
            message:   Platform-specific message pointer.
        """
        if eventType == b"windows_generic_MSG":
            import ctypes  # noqa: PLC0415
            import ctypes.wintypes  # noqa: PLC0415

            msg = ctypes.wintypes.MSG.from_address(int(message))
            if msg.message == 0x0084:  # WM_NCHITTEST
                from PySide6.QtGui import QCursor  # noqa: PLC0415

                pos = QCursor.pos()
                rect = self.frameGeometry()
                x, y = pos.x(), pos.y()
                left = rect.left()
                right = rect.right()
                top = rect.top()
                bottom = rect.bottom()
                b = self._BORDER

                on_left = x < left + b
                on_right = x > right - b
                on_top = y < top + b
                on_bottom = y > bottom - b

                if on_top and on_left:
                    result = 13  # HTTOPLEFT
                elif on_top and on_right:
                    result = 14  # HTTOPRIGHT
                elif on_bottom and on_left:
                    result = 16  # HTBOTTOMLEFT
                elif on_bottom and on_right:
                    result = 17  # HTBOTTOMRIGHT
                elif on_top:
                    result = 12  # HTTOP
                elif on_bottom:
                    result = 15  # HTBOTTOM
                elif on_left:
                    result = 10  # HTLEFT
                elif on_right:
                    result = 11  # HTRIGHT
                else:
                    return super().nativeEvent(eventType, message)

                return True, result

        return super().nativeEvent(eventType, message)


# ─────────────────────────────────────────────────────────────
#  ROUNDED BACKGROUND CONTAINER
# ─────────────────────────────────────────────────────────────

class _RoundedContainer(QWidget):
    """Transparent central widget that paints the themed rounded-rect background.

    By drawing the background here rather than on the :class:`QMainWindow`
    itself we avoid bleed artefacts at the window corners when
    ``WA_TranslucentBackground`` is set.
    """

    def paintEvent(self, event) -> None:  # type: ignore[override]
        """Fill the widget area with the current theme's deep-background colour."""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(_t().bg_deep))
        p.drawRoundedRect(
            self.rect(), AcouZApp._RADIUS, AcouZApp._RADIUS
        )
        p.end()


# ─────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ConfigManager.initialize()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)

    window = AcouZApp()
    window.show()
    sys.exit(app.exec())