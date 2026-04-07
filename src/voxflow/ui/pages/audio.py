"""
src/voxflow/ui/pages/audio.py

Audio settings page for the Voxflow application.

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

import sounddevice as sd

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QComboBox,
)
from PySide6.QtCore import Qt

import voxflow.ui.styles as S
from voxflow.ui.styles import Theme
from voxflow.ui.components import (
    _t, section_title, page_title, btn_ghost,
    make_svg, reload_svg, ToggleSwitch, SettingCard,
)
from voxflow.ui.pages.base import BasePage
from voxflow.utils.config import ConfigManager


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
        ``"Paramètres audio système par défaut"`` is always placed first
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
                name = "Paramètres audio système par défaut"

            if _EXCLUDE_PATTERN.search(name) and \
                    name != "Paramètres audio système par défaut":
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
    default = "Paramètres audio système par défaut"
    if default in result:
        result.remove(default)
        result.insert(0, default)

    return result or [default]


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
        if mic_name != "Paramètres audio système par défaut":
            for i, dev in enumerate(sd.query_devices()):
                if dev["name"] == mic_name:
                    device_id = i
                    break

        def _in_cb(indata, frames, time_info, status) -> None:  # noqa: ARG001
            buf.put(indata.copy())

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

        self._page_title_lbl = page_title("Audio")
        root.addWidget(self._page_title_lbl)
        root.addWidget(section_title("Périphérique d'entrée"))

        self._mic_card = SettingCard()

        # Microphone combo -------------------------------------------
        self._mic_combo = QComboBox()
        mics = get_real_microphones()
        self._mic_combo.addItems(mics if mics else ["Aucun microphone détecté"])
        saved = ConfigManager.get("MICROPHONE", "Paramètres audio système par défaut")
        if saved in mics:
            self._mic_combo.setCurrentText(saved)
        self._mic_combo.currentTextChanged.connect(
            lambda v: ConfigManager.set("MICROPHONE", v)
        )
        self._mic_card.add(
            "Microphone", "Source audio utilisée pour la dictée", self._mic_combo
        )

        # Test button -------------------------------------------------
        self._test_btn = btn_ghost("Tester le micro")
        self._test_btn.clicked.connect(self._toggle_test)
        self._mic_card.add(
            "Test Audio",
            "Écoutez votre retour vocal avec un léger décalage (0.5 s)",
            self._test_btn,
        )

        # Auxiliary toggles ------------------------------------------
        self._mic_card.add(
            "Suppression du bruit",
            "Filtrer les bruits de fond pour améliorer la précision",
            ToggleSwitch(True),
        )
        self._mic_card.add(
            "Annulation d'écho",
            "Évite que Voxflow capte la lecture audio en cours",
            ToggleSwitch(False),
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
            t: New :class:`~voxflow.ui.styles.Theme` to apply.
        """
        self._inner.setStyleSheet("background: transparent;")
        self._page_title_lbl.setStyleSheet(S.page_title_style(t))
        self._mic_card.setStyleSheet(S.card_qss(t))
        # Test button: restore ghost style (don't reset if active — user sees it)
        if not self._mic_tester.is_running:
            self._test_btn.setStyleSheet(S.btn_ghost_qss(t))

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _toggle_test(self) -> None:
        """Start or stop the microphone loopback test."""
        if self._mic_tester.is_running:
            self._mic_tester.stop()
            self._test_btn.setText("Tester le micro")
            self._test_btn.setStyleSheet(S.btn_ghost_qss(_t()))
        else:
            self._mic_tester.start(self._mic_combo.currentText())
            self._test_btn.setText("Arrêter le test (retour 0.5 s)")
            self._test_btn.setStyleSheet(
                "QPushButton { color: #EF4444; border: 1px solid #EF4444; "
                "background: rgba(239, 68, 68, 0.10); border-radius: 4px; "
                "padding: 6px 12px; font-weight: bold; }"
            )
