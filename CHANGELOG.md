# Changelog

All notable changes to Voxflow are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.0.0] — 2026-04-08

### Added

#### Core
- Global hotkeys using raw Windows scan codes (bypasses locale key names)
- In-memory audio capture via `sounddevice` (no temporary files written to disk)
- Groq Whisper `whisper-large-v3-turbo` for speech-to-text
- Groq `llama-3.3-70b-versatile` as a strict transcript-cleaner LLM
  - Adds punctuation, capitalisation, removes filler words
  - Converts spoken lists / emojis to text equivalents
  - System-level prompt injection resistance (7 absolute rules, temperature 0.1)
- Context-aware dictation: reads foreground selection via `uiautomation` before transcribing
- Clipboard-based text injection (`Ctrl+V`) for reliable Unicode support
- `cancel_recording()` on `DictationEngine` — hotkey cancel without API call

#### UI
- PySide6 frameless window with manual resize (8-zone `WM_NCHITTEST`)
- Live DARK / LIGHT theme switch with 280 ms cross-fade (screenshot-overlay technique)
- `BasePage` / `retheme()` contract — no widget rebuilt on theme switch, all state preserved
- Five settings pages: Home, General, API, Audio, About
- `StyledComboBox` with fully rounded popup (no OS rectangular border)
- `HotkeyButton` / `HotkeyRecorder` for in-app hotkey rebinding
- `VoiceOverlay` — themed floating pill (dark + light), animated VU-meter bars,
  ✕ cancel button (left) + ✓ confirm button (right), SVG icons only
- `_ThemeFloatBtn` — floating sun/moon toggle button, always on top across tab switches
- System tray icon (rendered from `LOGO_SVG` at runtime)
- Application logo: V-as-microphone housing, gradient background, grille lines
- `LOGO_SVG` embedded as a Python string constant (PyInstaller bundle safe)
- `_make_app_icon()` renders multi-resolution `QIcon` from `LOGO_SVG` at startup

#### Settings pages
- **General**: hotkey binding, hold/toggle mode, language selector, confirmation sound toggle,
  overlay toggle, *Launch at Windows startup* toggle (`winreg HKCU`)
- **API**: Groq API key field with live connection test
- **Audio**: physical microphone selector (virtual cables filtered out), 0.5 s loopback test
- **About**: version badge (accent-coloured, visible in both themes), GitHub / issue links,
  background update checker (GitHub Releases API)

#### Build
- `main.py` — clean entry point for dev and PyInstaller frozen modes
- `voxflow.spec` — PyInstaller one-folder spec (sounddevice DLL auto-located, all hidden imports)
- `create_icon.py` — generates `assets/icon.ico` from `assets/logo.svg` via PySide6 + Pillow

### Fixed
- `self.stream` → `self._stream` inconsistency in `DictationEngine`
- Duplicate `get_real_microphones()` definition removed (audio.py)
- Duplicate `_on_hotkey_released` definition removed (app.py)
- Dead code after early `return` in `make_page_api()` removed
- Hotkey chip background/border colour: Qt AARRGGBB byte-order bug fixed
  (`#accent18` → `#18rrggbb` — alpha byte must come first)
- Hotkey chip hover: removed `border-color: {accent}55` (same AARRGGBB issue)
- Dropdown popup black rectangle: `WA_TranslucentBackground` must be set before
  native window handle creation — moved flag patching to `StyledComboBox.__init__`
- Theme button unclickable after tab switch: added `raise_()` on `_ThemeFloatBtn` in `_go()`
- Hotkey chip vertical overflow: `(16, 0, 16, 0)` margins → `(14, 8, 14, 8)` + `AlignVCenter`
- About page `retheme()` no longer calls `setStyleSheet` on `QSvgWidget` (unsupported)

### Changed
- Sidebar version badge: `alpha` → `v1.0.0`
- Both badges in About page use `t.accent` (was `t.text_3`, invisible in light mode)
- Overlay removed "EN LIGNE" badge (redundant)
- LLM temperature: `0.3` → `0.1`
- Emojis in dictation mode labels replaced with inline SVG icons
- Fake "Noise suppression" and "Echo cancellation" toggles removed from Audio page

---

## [0.2.0-alpha] — 2025-11-XX

### Added
- PySide6 GUI with sidebar navigation
- Settings persistence via `.env` / `ConfigManager`
- System tray (background process, minimise-to-tray)
- Dictation history (last 10 sessions)
- Confirmation chime on start/stop

---

## [0.1.0-alpha] — 2025-09-XX

### Added
- Initial MVP: hotkey → Groq Whisper → clipboard paste
