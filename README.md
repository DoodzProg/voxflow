# Voxflow 🎙️

> **Open-source, self-hosted AI dictation for Windows.**  
> Hold a hotkey, speak — Voxflow transcribes, cleans, and types your text instantly.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2011-informational?logo=windows)](https://www.microsoft.com/windows)
[![API: Groq](https://img.shields.io/badge/API-Groq-orange)](https://console.groq.com/)
[![Status](https://img.shields.io/badge/Status-alpha%20v0.2.0-yellow)]()

---

## Overview

Voxflow is a lightweight Windows background process that replaces paid dictation tools (e.g. Typeless) with a fully local, hotkey-driven pipeline:

```
Hold Right Ctrl + Right Shift  →  Speak  →  Release  →  Text appears instantly
```

Under the hood:
1. **Whisper** (via Groq API) converts your voice to raw text at near-zero latency.
2. **Llama 3.3** (via Groq API) cleans hesitations, fixes punctuation, and executes smart commands (e.g. *"reply to this email saying I'm available tomorrow"*).
3. The polished text is injected via the clipboard at your cursor — works in any application.

**Why Groq?** Their free tier delivers Whisper + Llama inference in under 1 second — faster than most paid SaaS solutions.

---

## Features

- 🎤 **Hold-to-record** hotkey (`Right Ctrl + Right Shift`) — works globally, identical on AZERTY, QWERTY and QWERTZ layouts
- 🧹 **LLM post-processing** — removes filler words, formats lists, executes instructions
- 📋 **Context-aware** — optionally reads selected text before dictating to handle commands like "rewrite this"
- 💨 **In-memory audio** — no temporary files written to disk
- 🔑 **Secure config** — API key stored in `.env`, never hard-coded
- 🪶 **Runs silently** — system tray icon, no terminal window required

---

## Requirements

| Requirement | Details |
|---|---|
| OS | Windows 10 / 11 (64-bit) |
| Python | 3.11 or higher |
| Privileges | **Administrator** (required by the `keyboard` library for global hooks) |
| Groq API key | Free tier at [console.groq.com](https://console.groq.com/) |
| Microphone | Any microphone recognized by Windows |

---

## Installation

### 1 — Clone the repository

```bash
git clone https://github.com/DoodzProg/voxflow.git
cd voxflow
```

### 2 — Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### 4 — Configure your API key

Copy the example environment file and fill in your key:

```bash
copy .env.example .env
```

Edit `.env`:

```env
GROQ_API_KEY=gsk_your_key_here
```

Get a free key at [console.groq.com](https://console.groq.com/) — no credit card required.

---

## Usage

> ⚠️ **Administrator privileges are required.**  
> Right-click your terminal (PowerShell or CMD) → **"Run as administrator"**, then launch Voxflow.

```bash
venv\Scripts\activate
python src/voxflow/main.py
```

Voxflow starts silently in the system tray. The terminal can be minimised or closed.

### Hotkey reference

| Action | Hotkey |
|---|---|
| Start / stop dictation | Hold `Right Ctrl + Right Shift`, release to process |
| Quit Voxflow | Right-click tray icon → **Quit** |

> **Why Right Ctrl + Right Shift?**  
> This combination uses physical scan codes, making it layout-agnostic — it works identically on AZERTY, QWERTY, and QWERTZ keyboards without any configuration.

### Context-aware commands

Before pressing the hotkey, **select any text** in your active window. Voxflow will read it as context and pass it to the LLM alongside your dictation.

**Examples:**

- Select an email draft → dictate *"shorten this to three sentences"*
- Select a paragraph → dictate *"translate this to English"*
- No selection → dictate freely and Voxflow will clean and format your speech

---

## Configuration

All settings are at the top of `src/voxflow/main.py`:

| Variable | Default | Description |
|---|---|---|
| `WHISPER_MODEL` | `whisper-large-v3` | Groq STT model |
| `LLM_MODEL` | `llama-3.3-70b-versatile` | Groq LLM model |
| `SAMPLE_RATE` | `16000` | Audio sample rate (Hz) — do not change |
| `CHANNELS` | `1` | Audio channels (mono) |
| `HOTKEY_PRESS` | `right ctrl+right shift` | Hotkey to start recording |

The `SYSTEM_PROMPT` constant controls LLM behavior. Edit it to customize formatting rules, output language, or add domain-specific instructions.

---

## Project Structure

```
voxflow/
├── src/
│   └── voxflow/
│       ├── __init__.py
│       └── main.py         ← Core application
├── assets/
│   └── demo.gif            ← (planned)
├── .env.example            ← Environment variable template
├── .editorconfig           ← Editor consistency settings
├── CHANGELOG.md            ← Version history
├── CONTRIBUTING.md         ← Contribution guidelines
├── LICENSE                 ← MIT License
├── README.md
└── requirements.txt
```

---

## Roadmap

- [x] Working Windows MVP with Groq STT + LLM pipeline
- [x] System tray icon — runs fully headless
- [x] Cross-layout hotkey (`Right Ctrl + Right Shift`)
- [ ] Configurable hotkey via `config.toml`
- [ ] Self-hosted STT backend on Oracle Cloud (Whisper.cpp)
- [ ] Automatic fallback to Groq when self-hosted server is unreachable
- [ ] Android custom keyboard (IME) with dictation button
- [ ] Multiple language support
- [ ] Windows installer (NSIS or WiX)

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

---

## License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

*Built with ☕ as a free alternative to paid dictation tools.*