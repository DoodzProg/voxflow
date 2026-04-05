"""
Voxflow - Intelligent Voice Dictation & Processing

Author: Gaëtan (DoodzProg) - assisted by Claude & Gemini
Repository: https://github.com/DoodzProg/voxflow
License: MIT

Description:
    A localized, hotkey-driven voice typing assistant. It captures audio 
    via microphone, processes it through Groq's Whisper API for speech-to-text, 
    and refines the output using Llama-3 before simulating keyboard input 
    to type the polished text directly into the active window.
    
    This version uses the `keyboard` library for low-level Windows scan-code 
    hooks to reliably support AltGr on international/AZERTY layouts.
"""

import io
import os
import time
import threading
import queue
import numpy as np
import sounddevice as sd
import pyperclip
from scipy.io import wavfile
import keyboard  # Low-level Windows keyboard hook (scan-code based)
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY or GROQ_API_KEY == "en_attente_de_la_cle":
    raise ValueError("CRITICAL: GROQ_API_KEY is missing or invalid in the .env file.")

# Groq Models
WHISPER_MODEL = "whisper-large-v3"
LLM_MODEL = "llama-3.3-70b-versatile"

# Audio Settings
SAMPLE_RATE = 16000   # Hz — optimal for Whisper
CHANNELS = 1          # Mono

# System prompt for Llama-3
SYSTEM_PROMPT = """Tu es un assistant de dictée vocale intelligent.
Tu reçois une transcription brute de la voix de l'utilisateur.
Ton rôle est de :
1. Supprimer les hésitations ("euh", "hm", répétitions involontaires)
2. Corriger la ponctuation et la capitalisation
3. Formater intelligemment : créer des listes si l'utilisateur énumère, 
   créer des paragraphes si c'est un long texte
4. Si l'utilisateur donne une instruction (ex: "réponds à ce mail en disant X"),
   et qu'un contexte de texte sélectionné est fourni, EXÉCUTE l'instruction
   et retourne uniquement le texte final à insérer
5. Retourner UNIQUEMENT le texte final, sans commentaire ni explication.

Si un contexte (texte sélectionné) est fourni, utilise-le pour mieux comprendre
la demande de l'utilisateur."""

# ─────────────────────────────────────────────
# GLOBAL STATE
# ─────────────────────────────────────────────

class AppState:
    """Shared application state, protected by a threading lock."""
    def __init__(self) -> None:
        self.is_recording: bool = False
        self.audio_frames: list = []
        self.lock = threading.RLock()
        self.pipeline_queue: queue.Queue = queue.Queue()

state = AppState()
groq_client = Groq(api_key=GROQ_API_KEY)

# ─────────────────────────────────────────────
# AUDIO CAPTURE
# ─────────────────────────────────────────────

def audio_callback(indata, frames, time_info, status):
    """Called by sounddevice for each audio chunk."""
    if status:
        print(f"[Audio] Warning: {status}")
    with state.lock:
        if state.is_recording:
            state.audio_frames.append(indata.copy())

def get_audio_as_wav_bytes():
    """Assembles audio frames into WAV bytes in memory."""
    with state.lock:
        if not state.audio_frames:
            return None
        audio_data = np.concatenate(state.audio_frames, axis=0)

    audio_int16 = (audio_data * 32767).astype(np.int16)
    buffer = io.BytesIO()
    wavfile.write(buffer, SAMPLE_RATE, audio_int16)
    buffer.seek(0)
    return buffer

# ─────────────────────────────────────────────
# GROQ PIPELINE (STT → LLM)
# ─────────────────────────────────────────────

def run_pipeline(audio_bytes, selected_context):
    """Executes the STT and LLM processing via Groq API."""
    print("[Pipeline] Sending to Whisper...")

    # Step 1: STT with Whisper
    try:
        transcription_response = groq_client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=("audio.wav", audio_bytes, "audio/wav"),
            language="fr",
            response_format="text"
        )
        raw_text = transcription_response.strip()
        print(f"[Whisper] Raw: {raw_text}")
    except Exception as e:
        print(f"[Error Whisper] {e}")
        return

    if not raw_text:
        print("[Pipeline] Empty transcription, aborting.")
        return

    # Step 2: Clean / Format with Llama-3
    user_message = f"Transcription brute : {raw_text}"
    if selected_context:
        user_message += f"\n\nContexte (texte sélectionné avant la dictée) :\n{selected_context}"

    print("[Pipeline] Sending to Llama-3...")
    try:
        chat_response = groq_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=1024
        )
        final_text = chat_response.choices[0].message.content.strip()
        print(f"[Llama-3] Final: {final_text}")
    except Exception as e:
        print(f"[Error Llama-3] {e}")
        final_text = raw_text

    # Step 3: Type the text
    type_text(final_text)

def pipeline_worker():
    """Background thread consuming the pipeline queue."""
    while True:
        task = state.pipeline_queue.get()
        if task is None:
            break
        audio_bytes, context = task
        run_pipeline(audio_bytes, context)
        state.pipeline_queue.task_done()

# ─────────────────────────────────────────────
# KEYBOARD HOOKS & TYPING LOGIC
# ─────────────────────────────────────────────

def get_selected_text() -> str | None:
    """Attempt to retrieve the currently selected text via the clipboard."""
    try:
        previous_clipboard: str = pyperclip.paste()
        keyboard.send("ctrl+c")
        time.sleep(0.15)
        selected: str = pyperclip.paste()
        pyperclip.copy(previous_clipboard)

        if selected and selected != previous_clipboard:
            print(f"[Context] Selected text detected: {selected[:60]}...")
            return selected
    except Exception as exc:
        print(f"[Context] Could not read selection: {exc}")
    return None

def type_text(text: str) -> None:
    """Insert text at the current cursor position via the clipboard."""
    print("[Type] Inserting text...")
    previous_clipboard: str = ""
    try:
        previous_clipboard = pyperclip.paste()
    except Exception:
        pass

    pyperclip.copy(text)
    time.sleep(0.05)
    keyboard.send("ctrl+v")
    time.sleep(0.1)

    try:
        pyperclip.copy(previous_clipboard)
    except Exception:
        pass
    print("[Type] ✅ Text inserted.")

def _on_hotkey_press() -> None:
    """Callback invoked when AltGr + ; is pressed."""
    with state.lock:
        if not state.is_recording:
            print("\n[🎙️] Recording started...")
            state.is_recording = True
            state.audio_frames = []

def _on_hotkey_release() -> None:
    """Callback invoked when AltGr + ; is released."""
    with state.lock:
        if not state.is_recording:
            return

        print("[⏹️] Recording stopped. Processing...")
        state.is_recording = False
        audio_bytes = get_audio_as_wav_bytes()

    if audio_bytes is None:
        print("[Pipeline] No audio captured — aborting.")
        return

    context: str | None = get_selected_text()
    state.pipeline_queue.put((audio_bytes, context))

# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

def main() -> None:
    print("=" * 55)
    print("  Voxflow — Open-Source AI Dictation (Groq Edition)")
    print("=" * 55)
    print(f"  Hotkey  : AltGr + ;")
    print(f"  STT     : {WHISPER_MODEL}  (Groq)")
    print(f"  LLM     : {LLM_MODEL}  (Groq)")
    print(f"  Lang    : French (fr)")
    print("=" * 55)
    print("  Hold AltGr + ; to dictate. Ctrl+C to quit.\n")

    worker_thread = threading.Thread(target=pipeline_worker, daemon=True)
    worker_thread.start()

    keyboard.add_hotkey("altgr+;", _on_hotkey_press, suppress=True, trigger_on_release=False)
    keyboard.on_release_key(";", lambda _: _on_hotkey_release() if keyboard.is_pressed("altgr") else None, suppress=False)

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32",
        callback=audio_callback, blocksize=1024
    ):
        print("[System] Audio stream active. Hotkeys registered.")
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            print("\n[System] Shutdown requested. Goodbye!")
            state.pipeline_queue.put(None)

if __name__ == "__main__":
    main()