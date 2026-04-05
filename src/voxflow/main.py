"""
Voxflow - Intelligent Voice Dictation & Processing
===================================================

Author      : Gaëtan (DoodzProg) — assisted by Claude & Gemini
Repository  : https://github.com/DoodzProg/voxflow
License     : MIT

Description
-----------
A hotkey-driven AI dictation assistant for Windows.
Captures microphone audio, transcribes it via Groq Whisper, refines the
output with Llama-3, and injects the polished text at the cursor position.

Phase 1 — System Tray Integration
----------------------------------
The application runs as a background process with a system tray icon.
No terminal window is required during normal use.

Thread architecture
-------------------
  Main thread   : pystray icon event loop (required by Windows tray API)
  Worker thread : pipeline_worker — consumes the audio queue (STT → LLM → type)
  Audio thread  : sounddevice InputStream callback (managed by sounddevice)
  Keyboard hook : keyboard library low-level hook (managed internally)

Requirements
------------
  pip install groq sounddevice numpy keyboard pyperclip scipy pystray Pillow python-dotenv
"""

import io
import os
import sys
import time
import threading
import queue
from typing import Optional

import numpy as np
import sounddevice as sd
import pyperclip
import keyboard
from scipy.io import wavfile
from groq import Groq
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import pystray

# ── Environment ───────────────────────────────────────────────────────────────

load_dotenv()

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    # Fail fast with a clear message before the tray icon ever appears.
    sys.exit(
        "[FATAL] GROQ_API_KEY is missing or empty.\n"
        "Create a .env file with: GROQ_API_KEY=gsk_your_key_here"
    )

# ── Configuration ─────────────────────────────────────────────────────────────

# Groq model identifiers
WHISPER_MODEL: str = "whisper-large-v3"
LLM_MODEL: str = "llama-3.3-70b-versatile"

# Audio capture settings
SAMPLE_RATE: int = 16_000   # Hz — optimal for Whisper
CHANNELS: int = 1            # Mono

# Hotkey combination — Right Ctrl + Right Shift.
# Chosen for cross-layout compatibility (identical scan codes on AZERTY,
# QWERTY, QWERTZ) and one-handed ergonomics (both keys on the right side).
# Key names are locale-dependent on Windows — French OS returns French names.
# Confirmed via keyboard.hook() diagnostic on this machine.
HOTKEY_PRESS: str = "ctrl droite+right shift"
HOTKEY_RELEASE_KEY: str = "right shift"

# System prompt governing LLM post-processing behaviour
SYSTEM_PROMPT: str = """You are an intelligent voice dictation assistant.
You receive a raw voice transcription from the user.
Your role is to:
1. Remove filler words and involuntary repetitions ("euh", "hm", etc.)
2. Fix punctuation and capitalisation
3. Format intelligently: create bullet lists when the user enumerates,
   create paragraphs for longer dictations
4. If the user gives an instruction (e.g. "reply to this email saying X")
   and a selected-text context is provided, EXECUTE the instruction and
   return only the final text to be inserted
5. Return ONLY the final text — no commentary, no explanation.

If a context (text selected before dictation) is provided, use it to better
understand the user's intent."""

# ── Shared Application State ──────────────────────────────────────────────────

class AppState:
    """
    Thread-safe container for all mutable application state.

    Uses ``threading.RLock`` so that the audio callback and keyboard hooks
    (which run in separate threads) can safely read and mutate shared data
    without deadlocking when re-entrant acquisition occurs.

    Attributes
    ----------
    is_recording : bool
        True while the microphone is actively capturing frames.
    audio_frames : list[numpy.ndarray]
        Raw PCM chunks accumulated during a recording session.
    lock : threading.RLock
        Reentrant lock guarding ``is_recording`` and ``audio_frames``.
    pipeline_queue : queue.Queue
        Delivers ``(audio_bytes, context)`` tuples to the pipeline worker.
    """

    def __init__(self) -> None:
        self.is_recording: bool = False
        self.audio_frames: list = []
        self.lock: threading.RLock = threading.RLock()
        self.pipeline_queue: queue.Queue = queue.Queue()


state = AppState()
groq_client = Groq(api_key=GROQ_API_KEY)

# ── Audio Capture ─────────────────────────────────────────────────────────────

def audio_callback(
    indata: np.ndarray,
    frames: int,          # noqa: ARG001 — required by sounddevice signature
    time_info: object,    # noqa: ARG001
    status: sd.CallbackFlags,
) -> None:
    """
    sounddevice stream callback — called on every audio block.

    Appends a copy of the incoming PCM block to ``state.audio_frames`` while
    a recording session is active.  Runs in the sounddevice audio thread.

    Parameters
    ----------
    indata:
        Numpy array of shape ``(frames, channels)`` containing raw PCM data.
    status:
        Flags indicating driver-level overflow or underflow conditions.
    """
    if status:
        print(f"[Audio] Stream warning: {status}")
    with state.lock:
        if state.is_recording:
            state.audio_frames.append(indata.copy())


def get_audio_as_wav_bytes() -> Optional[io.BytesIO]:
    """
    Assemble captured audio frames into an in-memory WAV buffer.

    All audio remains in RAM — no temporary files are written to disk.

    Returns
    -------
    io.BytesIO | None
        A seeked WAV buffer ready for the Groq API, or ``None`` if no
        frames were captured during the recording session.
    """
    with state.lock:
        if not state.audio_frames:
            return None
        audio_data = np.concatenate(state.audio_frames, axis=0)

    audio_int16 = (audio_data * 32_767).astype(np.int16)
    buffer = io.BytesIO()
    wavfile.write(buffer, SAMPLE_RATE, audio_int16)
    buffer.seek(0)
    return buffer

# ── Groq Pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(audio_bytes: io.BytesIO, selected_context: Optional[str]) -> None:
    """
    Execute the full STT → LLM → type pipeline for one dictation session.

    Steps
    -----
    1. Send WAV audio to Groq Whisper for speech-to-text.
    2. Pass the raw transcript (and optional context) to Llama-3 for
       cleaning, formatting, or command execution.
    3. Inject the final text at the cursor via the clipboard.

    Parameters
    ----------
    audio_bytes:
        In-memory WAV buffer produced by ``get_audio_as_wav_bytes()``.
    selected_context:
        Text that was selected in the active window before dictation began,
        or ``None`` if nothing was selected.
    """
    print("[Pipeline] Sending audio to Whisper...")

    # Step 1: Speech-to-Text
    try:
        transcription = groq_client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=("audio.wav", audio_bytes, "audio/wav"),
            language="fr",
            response_format="text",
        )
        raw_text: str = transcription.strip()
        print(f"[Whisper] Raw transcript: {raw_text}")
    except Exception as exc:
        print(f"[Whisper] API error: {exc}")
        return

    if not raw_text:
        print("[Pipeline] Empty transcription — aborting.")
        return

    # Step 2: LLM post-processing
    user_message = f"Transcription brute : {raw_text}"
    if selected_context:
        user_message += (
            f"\n\nContexte (texte sélectionné avant la dictée) :\n{selected_context}"
        )

    print("[Pipeline] Sending transcript to Llama-3...")
    try:
        response = groq_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        final_text: str = response.choices[0].message.content.strip()
        print(f"[Llama-3] Processed text: {final_text}")
    except Exception as exc:
        print(f"[Llama-3] API error: {exc}")
        # Graceful degradation: fall back to unprocessed transcript.
        final_text = raw_text

    # Step 3: Inject text at cursor
    type_text(final_text)


def pipeline_worker() -> None:
    """
    Long-running background thread that drains the pipeline queue.

    Blocks on ``state.pipeline_queue.get()`` until a task arrives, then
    calls ``run_pipeline()``.  A ``None`` sentinel signals a clean shutdown.
    """
    while True:
        task = state.pipeline_queue.get()
        if task is None:
            print("[Worker] Shutdown signal received — exiting.")
            break
        audio_bytes, context = task
        run_pipeline(audio_bytes, context)
        state.pipeline_queue.task_done()

# ── Keyboard Hooks & Text Injection ──────────────────────────────────────────

def get_selected_text() -> Optional[str]:
    """
    Attempt to capture the currently selected text via the system clipboard.

    Sends ``Ctrl+C``, waits for the OS to update the clipboard, then reads
    the result.  The clipboard is restored to its previous content afterward.

    Returns
    -------
    str | None
        The selected text if it differs from the pre-capture clipboard
        content, otherwise ``None``.
    """
    try:
        previous: str = pyperclip.paste()
        keyboard.send("ctrl+c")
        time.sleep(0.15)
        selected: str = pyperclip.paste()
        pyperclip.copy(previous)

        if selected and selected != previous:
            print(f"[Context] Selected text: {selected[:60]}...")
            return selected
    except Exception as exc:
        print(f"[Context] Could not read selection: {exc}")
    return None


def type_text(text: str) -> None:
    """
    Inject *text* at the current cursor position using the clipboard.

    Clipboard-based injection (copy → Ctrl+V) is more reliable than
    simulating individual keystrokes, especially for accented characters
    and multi-line content.

    Parameters
    ----------
    text:
        The fully processed string to insert into the active window.
    """
    print("[Type] Injecting text via clipboard...")
    previous: str = ""
    try:
        previous = pyperclip.paste()
    except Exception:
        pass

    pyperclip.copy(text)
    time.sleep(0.05)
    keyboard.send("ctrl+v")
    time.sleep(0.1)

    try:
        pyperclip.copy(previous)
    except Exception:
        pass

    print("[Type] Text injected successfully.")


def _on_hotkey_press() -> None:
    """
    Keyboard hook callback — fired when ``Right Ctrl + Right Shift`` is pressed.

    Starts a new recording session if one is not already active.
    Executes in the keyboard library's internal hook thread.
    """
    with state.lock:
        if not state.is_recording:
            print("[Hotkey] Recording started.")
            state.is_recording = True
            state.audio_frames = []


def _on_hotkey_release() -> None:
    """
    Keyboard hook callback — fired when ``Right Ctrl + Right Shift`` is released.

    Stops the active recording session and enqueues the captured audio
    alongside any clipboard context for asynchronous pipeline processing.
    Executes in the keyboard library's internal hook thread.
    """
    with state.lock:
        if not state.is_recording:
            return
        print("[Hotkey] Recording stopped.")
        state.is_recording = False
        audio_bytes = get_audio_as_wav_bytes()

    if audio_bytes is None:
        print("[Hotkey] No audio captured — aborting.")
        return

    context: Optional[str] = get_selected_text()
    state.pipeline_queue.put((audio_bytes, context))

# ── System Tray Icon ──────────────────────────────────────────────────────────

def _build_tray_icon() -> Image.Image:
    """
    Generate the system tray icon programmatically using Pillow.

    Produces a 64×64 RGBA image: dark background with a stylised
    white "V" glyph representing Voxflow.

    Returns
    -------
    PIL.Image.Image
        The rendered tray icon, ready to pass to ``pystray.Icon``.
    """
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background — rounded square with brand colour (#5B4FCF, purple)
    bg_color = (91, 79, 207, 255)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=12, fill=bg_color)

    # "V" glyph — two diagonal white lines meeting at the bottom centre
    white = (255, 255, 255, 255)
    lw = 5  # stroke width
    # Left arm of the V
    draw.line([(10, 12), (32, 52)], fill=white, width=lw)
    # Right arm of the V
    draw.line([(54, 12), (32, 52)], fill=white, width=lw)

    return img


def _on_quit(icon: pystray.Icon, item: pystray.MenuItem) -> None:  # noqa: ARG001
    """
    System tray menu action — clean application shutdown.

    Sends a ``None`` sentinel to the pipeline worker so it can exit its
    loop gracefully, unhooks all keyboard listeners, and stops the tray icon
    (which unblocks ``icon.run()`` in the main thread, allowing the process
    to terminate).

    Parameters
    ----------
    icon:
        The ``pystray.Icon`` instance that owns this menu.
    item:
        The ``pystray.MenuItem`` that was activated (unused).
    """
    print("[Tray] Quit requested — shutting down...")
    state.pipeline_queue.put(None)   # Signal pipeline worker to stop
    keyboard.unhook_all()            # Release all keyboard hooks
    icon.stop()                      # Unblocks icon.run() → main() returns

# ── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
    """
    Application entry point.

    Initialisation sequence
    -----------------------
    1. Start the pipeline worker thread (daemon, stops with the process).
    2. Register ``Right Ctrl + Right Shift`` press/release keyboard hooks.
    3. Open the sounddevice audio input stream.
    4. Build the system tray icon and call ``icon.run()``.

    ``icon.run()`` blocks the main thread and drives the Windows tray message
    pump — this is required by the Win32 Shell_NotifyIcon API.  All other
    work happens in daemon threads or the keyboard hook thread.

    The application exits when the user selects "Quit" from the tray menu,
    which calls ``icon.stop()`` and unblocks this function.
    """
    print("=" * 55)
    print("  Voxflow — Open-Source AI Dictation (Groq Edition)")
    print("=" * 55)
    print(f"  Hotkey  : Right Ctrl + Right Shift")
    print(f"  STT     : {WHISPER_MODEL}")
    print(f"  LLM     : {LLM_MODEL}")
    print(f"  Lang    : French (fr)")
    print("=" * 55)
    print("  Starting background services...\n")

    # 1. Pipeline worker (daemon — auto-killed if main thread exits unexpectedly)
    worker = threading.Thread(target=pipeline_worker, name="pipeline-worker", daemon=True)
    worker.start()

    # 2. Keyboard hooks — Right Ctrl (scan 29) + Right Shift (scan 54).
    # We use raw scan codes instead of key names to bypass locale-dependent
    # name resolution (French Windows returns 'ctrl droite', English returns
    # 'right ctrl' — scan codes are always identical regardless of locale).
    SCAN_CTRL_R  = 29
    SCAN_SHIFT_R = 54

    def _raw_hook(event: keyboard.KeyboardEvent) -> None:
        """Low-level hook — tracks Right Ctrl + Right Shift by scan code."""
        ctrl_held  = keyboard.is_pressed(SCAN_CTRL_R)
        shift_held = keyboard.is_pressed(SCAN_SHIFT_R)

        if event.event_type == keyboard.KEY_DOWN:
            # Both keys pressed → start recording
            if ctrl_held and shift_held:
                _on_hotkey_press()
        elif event.event_type == keyboard.KEY_UP:
            # Either key released while recording → stop
            if event.scan_code in (SCAN_CTRL_R, SCAN_SHIFT_R):
                _on_hotkey_release()

    keyboard.hook(_raw_hook)
    print("[System] Keyboard hooks registered.")

    # 3. Audio stream (runs permanently; callback fires only while recording)
    audio_stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        callback=audio_callback,
        blocksize=1024,
    )
    audio_stream.start()
    print("[System] Audio stream active.")

    # 4. System tray icon — MUST run on the main thread (Win32 requirement)
    tray_icon = pystray.Icon(
        name="Voxflow",
        icon=_build_tray_icon(),
        title="Voxflow — Hold Right Ctrl + Right Shift to dictate",
        menu=pystray.Menu(
            pystray.MenuItem("Voxflow  (Right Ctrl + Right Shift)", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", _on_quit),
        ),
    )

    print("[System] System tray icon starting — terminal can be minimised.\n")
    tray_icon.run()   # Blocks until _on_quit() calls icon.stop()

    # ── Cleanup (reached after icon.stop()) ───────────────────────────────────
    print("\n[System] Cleaning up...")
    audio_stream.stop()
    audio_stream.close()
    worker.join(timeout=5)
    print("[System] Shutdown complete. Goodbye!")


if __name__ == "__main__":
    main()