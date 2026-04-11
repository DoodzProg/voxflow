"""
AcouZ - Open-source AI voice dictation
Copyright (c) 2025-2026 DoodzProg
Licensed under the MIT License

src/acouz/ui/pages/audio.py

Audio settings page for the AcouZ application.

Provides microphone selection (filtered to real physical devices), a 0.5-second
loopback test, and auxiliary toggles (noise suppression, echo cancellation).

Classes:
    MicTester:  Thread-safe loopback audio engine.
    AudioPage:  PySide6 page widget.
"""

from __future__ import annotations

import queue
import re
import threading
import time
from typing import Optional

import numpy as np
import sounddevice as sd

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter

import acouz.ui.styles as S
from acouz.ui.styles import Theme
from acouz.ui.components import (
    _t, section_title, page_title, btn_ghost,
    make_svg, reload_svg, SettingCard, StyledComboBox,
)
from acouz.ui.pages.base import BasePage
from acouz.utils.config import ConfigManager
from acouz.utils.i18n import tr


# ─────────────────────────────────────────────────────────────
#  AUDIO DEVICE HELPERS
# ─────────────────────────────────────────────────────────────

#: Regex matching virtual / output / loopback device names to exclude.
_EXCLUDE_PATTERN = re.compile(
    r"output|hdmi|displayport|stereo mix|what u hear|loopback|"
    r"virtual|vb-audio|voicemeeter",
    re.IGNORECASE,
)


def get_real_microphones() -> list[str]:
    """Return only physical, connectable input devices.

    Applies a two-pass filter:

    1. **Name filter** — excludes known virtual / output device patterns.
    2. **Open probe** — attempts ``sd.InputStream`` on each candidate; any
       device that raises an exception (disconnected, blocked) is silently
       dropped.

    Duplicate names caused by Windows short-name truncation are deduplicated
    by retaining the longest (most descriptive) variant.

    Returns:
        Ordered list of microphone display names. The system-default entry
        ``"System Default"`` is always placed first
        when present.
    """
    valid: dict[str, int] = {}
    try:
        for i, dev in enumerate(sd.query_devices()):
            if dev["max_input_channels"] < 1:
                continue

            name: str = dev["name"]

            # Normalise the Windows default mapper entry
            if any(kw in name.lower() for kw in
                   ("mappeur", "mapper", "pilote de capture")):
                name = "System Default"

            if _EXCLUDE_PATTERN.search(name) and \
                    name != "System Default":
                continue

            # Live probe: open & immediately close a stream
            try:
                with sd.InputStream(device=i, channels=1, samplerate=16_000):
                    pass
            except Exception:
                continue

            # Deduplicate: keep the longest name among near-duplicates
            found = False
            for existing in list(valid.keys()):
                if name.startswith(existing) and len(name) > len(existing):
                    del valid[existing]
                    valid[name] = i
                    found = True
                    break
                elif existing.startswith(name):
                    found = True
                    break
            if not found:
                valid[name] = i

    except Exception as exc:
        print(f"[Audio] Device scan error: {exc}")

    result = list(valid.keys())
    default = "System Default"
    if default in result:
        result.remove(default)
        result.insert(0, default)

    return result or [default]


# ─────────────────────────────────────────────────────────────
#  MIC LEVEL BAR  (VU-meter shown during loopback test)
# ─────────────────────────────────────────────────────────────

class _MicLevelBar(QWidget):
    """Animated VU-meter bar widget for the microphone loopback test.

    Slightly wider than the overlay version (7 bars, 68×30 px) so it is
    readable even without active speakers.  The level is updated via a
    :class:`~PySide6.QtCore.QTimer` that polls
    :attr:`MicTester.current_level` on the main thread.
    """

    _BAR_COUNT = 7

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedSize(68, 30)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: transparent;")
        self._levels: list[float] = [0.0] * self._BAR_COUNT
        self._targets: list[float] = [0.0] * self._BAR_COUNT
        self._timer = QTimer(self)
        self._timer.setInterval(35)  # ~28 fps
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        """Begin the animation loop."""
        self._timer.start()

    def stop(self) -> None:
        """Stop the animation loop and reset all bars to zero."""
        self._timer.stop()
        self._levels  = [0.0] * self._BAR_COUNT
        self._targets = [0.0] * self._BAR_COUNT
        self.update()

    def push_level(self, rms: float) -> None:
        """Set a new target RMS level; bars animate toward it smoothly.

        Args:
            rms: Normalised RMS value in ``[0.0, 1.0]``.
        """
        import random  # noqa: PLC0415
        for i in range(self._BAR_COUNT):
            # Each bar gets a randomised fraction of the RMS for organic motion.
            self._targets[i] = min(1.0, rms * (0.5 + random.random() * 1.0))

    def _tick(self) -> None:
        """Smooth each bar toward its target via exponential decay."""
        changed = False
        for i in range(self._BAR_COUNT):
            diff = self._targets[i] - self._levels[i]
            self._levels[i] += diff * 0.28
            if abs(diff) > 0.005:
                changed = True
            # Decay toward zero when no new level is pushed.
            self._targets[i] *= 0.88
        if changed:
            self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        """Draw seven rounded bars whose heights scale with their level."""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)

        accent = QColor(_t().accent)
        bar_w, gap = 5, 4
        total_w = self._BAR_COUNT * bar_w + (self._BAR_COUNT - 1) * gap
        sx = (self.width() - total_w) // 2
        cy = self.height() // 2
        base_h, max_h = 4, 22

        for i, lvl in enumerate(self._levels):
            dist = abs(i - self._BAR_COUNT // 2)
            h = base_h + lvl * max_h * (1.0 - dist * 0.18)
            x = sx + i * (bar_w + gap)
            y = cy - h / 2
            color = QColor(accent)
            color.setAlphaF(0.25 + lvl * 0.75)
            p.setBrush(color)
            p.drawRoundedRect(int(x), int(y), bar_w, int(h), 2, 2)

        p.end()


# ─────────────────────────────────────────────────────────────
#  MIC TESTER
# ─────────────────────────────────────────────────────────────

class MicTester:
    """Thread-safe loopback audio engine with a 0.5-second artificial delay.

    Starts an :class:`~sounddevice.InputStream` for the selected microphone and
    routes captured frames to the default output, allowing the user to hear
    their own voice with a short latency offset (to avoid acoustic feedback at
    close range).

    Usage::

        tester = MicTester()
        tester.start("Casque (Realtek Audio)")
        # … user listens …
        tester.stop()
    """

    def __init__(self) -> None:
        self.is_running: bool = False
        self.current_level: float = 0.0
        self._thread: Optional[threading.Thread] = None

    def start(self, mic_name: str) -> None:
        """Start the loopback thread for the given microphone.

        If a test is already running, this call is a no-op.

        Args:
            mic_name: Display name as returned by :func:`get_real_microphones`.
        """
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(
            target=self._run, args=(mic_name,), daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """Signal the loopback thread to stop and wait for it to finish."""
        self.is_running = False
        self.current_level = 0.0
        if self._thread:
            self._thread.join(timeout=1.0)

    def _run(self, mic_name: str) -> None:
        """Internal: run the loopback audio loop in a background thread.

        Args:
            mic_name: Microphone display name.
        """
        buf: queue.Queue = queue.Queue()
        samplerate = 16_000

        device_id: Optional[int] = None
        if mic_name != "System Default":
            for i, dev in enumerate(sd.query_devices()):
                if dev["name"] == mic_name:
                    device_id = i
                    break

        def _in_cb(indata, frames, time_info, status) -> None:  # noqa: ARG001
            buf.put(indata.copy())
            self.current_level = float(np.sqrt(np.mean(indata ** 2))) * 8.0

        try:
            with sd.InputStream(
                device=device_id, channels=1,
                samplerate=samplerate, callback=_in_cb,
            ), sd.OutputStream(channels=1, samplerate=samplerate) as out:
                time.sleep(0.5)  # Artificial delay to prevent feedback
                while self.is_running:
                    try:
                        data = buf.get(timeout=0.1)
                        out.write(data)
                    except queue.Empty:
                        continue
        except Exception as exc:
            print(f"[Audio] Loopback test error: {exc}")


# ─────────────────────────────────────────────────────────────
#  AUDIO PAGE
# ─────────────────────────────────────────────────────────────

class AudioPage(BasePage):
    """Audio settings page for microphone selection and loopback testing.

    Args:
        parent: Optional parent widget.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._mic_tester = MicTester()
        self._build()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build(self) -> None:
        """Build the audio settings page layout."""
        t = _t()
        self._inner = QWidget()
        self._inner.setStyleSheet("background: transparent;")
        root = QVBoxLayout(self._inner)
        root.setContentsMargins(36, 36, 36, 36)
        root.setSpacing(24)

        self._page_title_lbl = page_title(tr("audio.title"))
        root.addWidget(self._page_title_lbl)
        self._sec_input = section_title(tr("audio.section.input"))
        root.addWidget(self._sec_input)

        self._mic_card = SettingCard()

        # Microphone combo -------------------------------------------
        self._mic_combo = StyledComboBox()
        self._mic_combo.setMaximumWidth(260)
        mics = get_real_microphones()
        # Add full names to dropdown but display truncated in the combo header
        for name in (mics if mics else [tr("audio.mic.none")]):
            display = (name[:28] + "…") if len(name) > 30 else name
            self._mic_combo.addItem(display, userData=name)
        saved = ConfigManager.get("MICROPHONE", "System Default")
        for i in range(self._mic_combo.count()):
            if self._mic_combo.itemData(i) == saved:
                self._mic_combo.setCurrentIndex(i)
                break
        self._mic_combo.currentIndexChanged.connect(
            lambda i: ConfigManager.set(
                "MICROPHONE", self._mic_combo.itemData(i) or self._mic_combo.itemText(i)
            )
        )
        self._mic_card.add(
            tr("audio.mic.label"), tr("audio.mic.desc"), self._mic_combo
        )

        # Test button row — [VU meter bar] + [button] in a container ----------
        self._test_container = QWidget()
        self._test_container.setStyleSheet("background: transparent;")
        _row = QHBoxLayout(self._test_container)
        _row.setContentsMargins(0, 0, 0, 0)
        _row.setSpacing(8)

        self._level_bar = _MicLevelBar()
        self._level_bar.setVisible(False)
        _row.addWidget(self._level_bar, 0, Qt.AlignVCenter)

        self._test_btn = btn_ghost(tr("audio.test.start"))
        self._test_btn.setFixedWidth(140)
        self._test_btn.setStyleSheet(S.btn_outlined_qss(_t()))
        self._test_btn.clicked.connect(self._toggle_test)
        _row.addWidget(self._test_btn, 0, Qt.AlignVCenter)

        self._mic_card.add(
            tr("audio.test.label"),
            tr("audio.test.desc"),
            self._test_container,
        )

        # Timer: polls current_level from audio thread → VU meter
        self._level_timer = QTimer(self)
        self._level_timer.setInterval(35)
        self._level_timer.timeout.connect(
            lambda: self._level_bar.push_level(
                min(1.0, self._mic_tester.current_level)
            )
        )

        root.addWidget(self._mic_card)
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
        self._mic_card.retheme(t)
        # Test button: restore ghost style (don't reset if active — user sees it)
        if not self._mic_tester.is_running:
            self._test_btn.setStyleSheet(S.btn_outlined_qss(t))

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def retranslate(self) -> None:
        """Update all visible text strings to the current UI language."""
        self._page_title_lbl.setText(tr("audio.title"))
        self._sec_input._title_lbl.setText(tr("audio.section.input").upper())
        mic_rows = self._mic_card.rows()
        if len(mic_rows) >= 2:
            mic_rows[0].set_texts(tr("audio.mic.label"),  tr("audio.mic.desc"))
            mic_rows[1].set_texts(tr("audio.test.label"), tr("audio.test.desc"))
        # Update test button text only when not actively running
        if not self._mic_tester.is_running:
            self._test_btn.setText(tr("audio.test.start"))

    def _toggle_test(self) -> None:
        """Start or stop the microphone loopback test."""
        if self._mic_tester.is_running:
            self._level_timer.stop()
            self._level_bar.stop()
            self._level_bar.setVisible(False)
            self._mic_tester.stop()
            self._test_btn.setText(tr("audio.test.start"))
            self._test_btn.setStyleSheet(S.btn_outlined_qss(_t()))
        else:
            _full_name = self._mic_combo.currentData() or self._mic_combo.currentText()
            self._mic_tester.start(_full_name)
            self._level_bar.setVisible(True)
            self._level_bar.start()
            self._level_timer.start()
            self._test_btn.setText(tr("audio.test.stop"))
            self._test_btn.setStyleSheet(
                "QPushButton { color: #EF4444; border: 1px solid #EF4444; "
                "background: rgba(239, 68, 68, 0.10); border-radius: 4px; "
                "padding: 6px 12px; font-weight: bold; }"
            )
