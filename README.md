# AcouZ

**Open-source AI-powered voice dictation — Windows (stable) · Linux/Ubuntu (in progress).**  
Hold a hotkey, speak, release — your words appear instantly in any application.

<p align="center">
  <img src="docs/assets/demo.gif" alt="AcouZ app walkthrough" width="720" />
</p>

> **v1.0.2** · [Download installer](https://github.com/DoodzProg/acouz/releases/latest) · [GitHub Pages](https://doodzprog.github.io/acouz/)

---

## Overview

AcouZ is a lightweight, privacy-friendly dictation assistant that runs entirely on your machine (except for the Groq API call). It captures audio from your microphone, transcribes it with **Groq Whisper**, optionally cleans and reformats it with **Groq Llama-3**, then injects the result at your cursor via the clipboard — in under a second.

No subscription, no cloud account beyond a free Groq API key, no data retained on external servers.

---

## Demo

<p align="center">
  <img src="docs/assets/example.gif" alt="AcouZ dictation in action" width="720" />
</p>

---

## Screenshots

| | |
|:---:|:---:|
| <img src="docs/assets/screenshot-home.png" alt="Dashboard" width="420"/> | <img src="docs/assets/screenshot-settings.png" alt="Settings" width="420"/> |
| *Dashboard — stats & shortcuts* | *Settings — hotkeys & language* |
| <img src="docs/assets/screenshot-audio.png" alt="Audio page" width="420"/> | <img src="docs/assets/screenshot-overlay.png" alt="Overlay" width="420"/> |
| *Audio — microphone & VU meter* | *Overlay — floating recording bubble* |

---

## Features

- **Hotkey-driven dictation** — customisable key combos (hold or toggle mode)
- **Context-aware instructions** — select text first, then dictate a command; the LLM responds using your selection as context
- **LLM post-processing** — automatic punctuation, capitalisation and filler-word removal
- **Physical microphone filter** — only real, connectable devices shown (no virtual cables, no loopback entries)
- **0.5 s loopback test** — hear your own mic with live VU-meter visualiser
- **Floating voice overlay** — animated VU-meter bubble shown during recording
- **Confirmation chimes** — soft two-note sound on start/stop (toggle-able)
- **Dictation history** — last 10 sessions with one-click copy
- **Live DARK / LIGHT theme** — instant switch, no reconstruction, state preserved
- **System tray** — runs silently in the background; window minimises to tray
- **Bilingual UI** — full English / French interface, switchable live without restart
- **Multi-language dictation** — Whisper language code configurable per user (EN, FR, ES, DE, IT)

---

## Architecture

```
src/acouz/
├── platform/
│   ├── __init__.py      # OS dispatcher — imports windows or linux backend at runtime
│   ├── windows.py       # Win32 implementations (DWM, user32, winreg, keyboard)
│   └── linux.py         # Linux stubs → full pynput/xdotool impl in Phase 2
├── core/
│   ├── engine.py        # DictationEngine (QThread) — STT + LLM pipeline
│   └── hotkey.py        # HotkeyListener (QThread) — 50 ms keyboard poll
├── ui/
│   ├── app.py           # AcouZApp (QMainWindow) + VoiceOverlay + entry point
│   ├── components.py    # Reusable widgets: NavButton, StatCard, HotkeyButton ...
│   ├── styles.py        # Theme dataclasses (DARK/LIGHT), ICONS dict, QSS helpers
│   └── pages/
│       ├── base.py      # BasePage(QScrollArea) — abstract retheme() contract
│       ├── home.py      # Dashboard: stats + shortcut cards + history
│       ├── general.py   # Hotkey binding, behaviour toggles, language
│       ├── api.py       # Groq API key configuration + live verification
│       ├── audio.py     # Microphone selection + loopback test (MicTester)
│       └── about.py     # Version info + project links
└── utils/
    └── config.py        # ConfigManager — reads/writes .env file
```

**Theme-switching design:** each page is a class inheriting `BasePage` with a `retheme(t: Theme)` method. `AcouZApp.apply_theme()` updates the global theme state, applies a new QPalette + QSS, then calls `retheme()` on every page — no widget is rebuilt, so all user-input state (API key field, selected microphone, toggles) is preserved across switches.

---

## Requirements

### Windows (stable)

| Requirement | Version |
|-------------|---------|
| Windows | 10 / 11 |
| Python | 3.11+ |
| Groq API key | Free tier (no credit card) |
| Admin privileges | Required for global keyboard hooks |

### Linux — Ubuntu (in progress, branch `feature/linux-port`)

| Requirement | Notes |
|-------------|-------|
| Ubuntu | 22.04+ (X11 or XWayland) |
| Python | 3.11+ |
| `portaudio19-dev` | PortAudio headers for `sounddevice` |
| `xdotool` + `xclip` | Foreground window detection + text capture (Phase 2) |
| `pynput` | Hotkey listener replacement for `keyboard` (Phase 2) |
| Groq API key | Same as Windows |

> **Note:** The application currently boots and renders on Linux.  
> Hotkeys, context capture, and autostart are stubs — full implementations  
> are tracked in `src/acouz/platform/linux.py` and will land in Phase 2–3.

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/DoodzProg/acouz.git
cd acouz

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your Groq API key
copy .env.example .env
# Edit .env and set GROQ_API_KEY=gsk_...
```

> **Tip:** You can also enter the key directly in the **API Groq** settings page inside the app — no manual file editing needed. Get a [free API key here](https://console.groq.com/keys).

---

## Usage

```bash
# Run the application
python main.py
# or
python src/AcouZ/ui/app.py
```

The app starts minimised to the system tray. Double-click the tray icon to open the settings window.

### Default Hotkeys

| Action | Hotkey |
|--------|--------|
| Dictation (hold) | `Right Ctrl` + `Right Shift` |
| Context dictation (hold) | `Right Alt` + `Right Shift` |

Both hotkeys are fully remappable in the **Settings** page.

### Dictation workflow

1. Place your cursor in any text field (browser, editor, chat app...)
2. Hold `Right Ctrl + Right Shift` and speak
3. Release — the transcribed, corrected text is pasted automatically

### Context-aware instructions

1. Select some text in the foreground application
2. Hold `Right Alt + Right Shift` and speak an instruction  
   *(e.g. "Reply that I'm available tomorrow afternoon")*
3. Release — the LLM rewrites or responds using the selection as context

---

## Configuration

All settings are persisted in `.env` at the project root.
They can also be changed live from the settings window.

| Key | Default | Description |
|-----|---------|-------------|
| `GROQ_API_KEY` | — | Your Groq API key |
| `WHISPER_MODEL` | `whisper-large-v3-turbo` | Groq STT model |
| `LLM_MODEL` | `llama-3.3-70b-versatile` | Groq LLM model for correction |
| `MICROPHONE` | system default | Selected microphone display name |
| `HOTKEY_DICTATE` | `right ctrl+right shift` | Dictation hotkey |
| `HOTKEY_CONTEXT` | `right alt+right shift` | Context dictation hotkey |
| `HOTKEY_DICTATE_MODE` | `hold` | `hold` or `toggle` |
| `HOTKEY_CONTEXT_MODE` | `hold` | `hold` or `toggle` |
| `CONFIRMATION_SOUND` | `true` | Play chime on start/stop |
| `UI_LANGUAGE` | `en` | Interface language (`en` or `fr`) |
| `DICTATION_LANGUAGE` | `en` | Transcription language — ISO 639-1 code passed to Whisper (`en`, `fr`, `es`, `de`, `it`) |

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.

### Quick start

```bash
git checkout -b feat/your-feature
# make your changes
git commit -m "feat: add your feature"
git push origin feat/your-feature
# open a pull request on GitHub
```

### Branch naming

| Prefix | Purpose |
|--------|---------|
| `feat/` | New feature |
| `fix/` | Bug fix |
| `docs/` | Documentation only |
| `refactor/` | Code restructuring |
| `chore/` | Build / tooling |

### Code standards

- Python 3.11+ with full **type hints**
- **Google-style docstrings** on every public function and class
- Line length: 100 characters (`black --line-length 100`)
- No emojis in Python source — use SVG icons from `styles.ICONS`

---

## Building

### Generate the application icon (once)

```bash
python create_icon.py
# Writes assets/icon.ico  (multi-resolution: 16 → 256 px)
```

### Build the standalone executable

```bash
pip install pyinstaller
pyinstaller AcouZ.spec
# Output: dist\AcouZ\AcouZ.exe
```

### Create a Windows installer with Inno Setup

Install [Inno Setup 6](https://jrsoftware.org/isinfo.php), then compile the provided script:

```bash
iscc installer.iss
# Output: dist\AcouZSetup.exe  (~15–20 MB)
```

The installer:
- Installs to `%LocalAppData%\AcouZ` (no admin rights required)
- Creates Start Menu and optional Desktop shortcuts
- Registers an uninstaller in *Add/Remove Programs*
- Honours the in-app *Launch at Windows startup* toggle (`HKCU` registry)

---

## Roadmap

### Cross-platform
- [x] Platform abstraction layer (`acouz.platform`) — Phase 0 complete
- [ ] Linux Phase 2 — `pynput` hotkeys, `xdotool` foreground detection, `xclip` text capture
- [ ] Linux Phase 3 — `~/.config/autostart` for launch-at-login
- [ ] Linux Phase 4 — Wayland strategy via `QT_QPA_PLATFORM=xcb` / XWayland
- [ ] Linux Phase 5 — Integration tests on Ubuntu
- [ ] Linux Phase 6 — `.AppImage` packaging

### Features
- [ ] Configurable Whisper language per dictation session
- [ ] Self-hosted STT via Whisper.cpp (offline mode)
- [ ] Multi-monitor overlay positioning
- [ ] History export (plain text / CSV)

---

## License

[MIT](LICENSE) — free for personal and commercial use.

---

*Built with [PySide6](https://doc.qt.io/qtforpython/), [Groq](https://groq.com/) and [sounddevice](https://python-sounddevice.readthedocs.io/).*
