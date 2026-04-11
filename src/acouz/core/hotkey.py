"""
AcouZ - Open-source AI voice dictation
Copyright (c) 2025-2026 DoodzProg
Licensed under the MIT License

Hotkey listener for the AcouZ application.

Polls the ``keyboard`` library at 50 ms intervals for the configured key
combinations and emits PySide6 signals so the UI thread can react safely.

Two independent hotkeys are monitored:

- **Dictate** (default ``right ctrl + right shift``) — starts/stops a plain
  dictation session.
- **Context** (default ``right alt + right shift``) — starts/stops a
  context-aware dictation session; also captures the active window HWND so
  the calling code can read the selected text from the correct application.

Both hotkeys support two trigger modes stored in
:class:`~acouz.utils.config.ConfigManager`:

- ``"hold"`` (Push-to-Talk): hold to record, release to transcribe.
- ``"toggle"`` (Toggle): first press starts, second press stops.
"""

from __future__ import annotations

import ctypes
import time
from typing import Optional

import keyboard
from PySide6.QtCore import QThread, Signal

from acouz.utils.config import ConfigManager


class HotkeyListener(QThread):
    """Background thread that monitors global keyboard state for AcouZ hotkeys.

    Signals:
        hotkey_dictate_pressed ():       Emitted when the dictate hotkey activates.
        hotkey_dictate_released ():      Emitted when the dictate hotkey deactivates.
        hotkey_context_pressed (int):    Emitted when the context hotkey activates;
                                         carries the HWND of the previously active window.
        hotkey_context_released ():      Emitted when the context hotkey deactivates.

    Args:
        parent: Optional parent :class:`~PySide6.QtCore.QObject`.
    """

    hotkey_dictate_pressed = Signal()
    hotkey_dictate_released = Signal()
    hotkey_context_pressed = Signal(int)
    hotkey_context_released = Signal()

    _POLL_INTERVAL: float = 0.05  # seconds between keyboard state checks

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._running: bool = True
        self._dictate_active: bool = False
        self._context_active: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def stop(self) -> None:
        """Signal the polling loop to exit and block until the thread finishes."""
        self._running = False
        self.wait()

    # ------------------------------------------------------------------
    # QThread run
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Main polling loop — runs until :meth:`stop` is called.

        Reads ``HOTKEY_DICTATE``, ``HOTKEY_CONTEXT``, ``HOTKEY_DICTATE_MODE``
        and ``HOTKEY_CONTEXT_MODE`` from
        :class:`~acouz.utils.config.ConfigManager` on every iteration so that
        hotkey changes take effect immediately without restarting the thread.
        """
        print("[HotkeyListener] Thread started.")

        dictate_was_pressed = False
        context_was_pressed = False
        dictate_recording = False
        context_recording = False
        last_hwnd: int = 0

        while self._running:
            try:
                dictate_str = ConfigManager.get(
                    "HOTKEY_DICTATE", "right ctrl+right shift"
                )
                context_str = ConfigManager.get(
                    "HOTKEY_CONTEXT", "right alt+right shift"
                )
                dictate_mode = ConfigManager.get("HOTKEY_DICTATE_MODE", "hold")
                context_mode = ConfigManager.get("HOTKEY_CONTEXT_MODE", "hold")

                d_keys = self._parse_keys(dictate_str)
                c_keys = self._parse_keys(context_str)

                d_pressed = all(keyboard.is_pressed(k) for k in d_keys)
                c_pressed = all(keyboard.is_pressed(k) for k in c_keys)

                # Capture foreground HWND only when no hotkey is active
                if not d_pressed and not c_pressed:
                    hwnd = ctypes.windll.user32.GetForegroundWindow()
                    if hwnd:
                        last_hwnd = hwnd

                # -- Dictate hotkey --
                if dictate_mode == "hold":
                    if d_pressed and not self._dictate_active:
                        self._dictate_active = True
                        self.hotkey_dictate_pressed.emit()
                    elif not d_pressed and self._dictate_active:
                        self._dictate_active = False
                        self.hotkey_dictate_released.emit()
                else:  # toggle
                    if d_pressed and not dictate_was_pressed:
                        if not dictate_recording:
                            dictate_recording = True
                            self.hotkey_dictate_pressed.emit()
                        else:
                            dictate_recording = False
                            self.hotkey_dictate_released.emit()
                    dictate_was_pressed = d_pressed

                # -- Context hotkey --
                if context_mode == "hold":
                    if c_pressed and not self._context_active:
                        self._context_active = True
                        self.hotkey_context_pressed.emit(last_hwnd)
                    elif not c_pressed and self._context_active:
                        self._context_active = False
                        self.hotkey_context_released.emit()
                else:  # toggle
                    if c_pressed and not context_was_pressed:
                        if not context_recording:
                            context_recording = True
                            self.hotkey_context_pressed.emit(last_hwnd)
                        else:
                            context_recording = False
                            self.hotkey_context_released.emit()
                    context_was_pressed = c_pressed

            except Exception as exc:
                print(f"[HotkeyListener] Error: {exc}")

            time.sleep(self._POLL_INTERVAL)

        print("[HotkeyListener] Thread stopped.")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_keys(hotkey_str: str) -> list[str]:
        """Normalise a hotkey string into a list of ``keyboard``-compatible key names.

        Strips ``"right "`` / ``"left "`` prefixes so that
        ``keyboard.is_pressed()`` matches both sides of modifier keys.

        Args:
            hotkey_str: Raw hotkey string, e.g. ``"right ctrl+right shift"``.

        Returns:
            List of normalised key name strings, e.g. ``["ctrl", "shift"]``.
        """
        return [
            k.strip().lower().replace("right ", "").replace("left ", "")
            for k in hotkey_str.split("+")
        ]
