# Changelog

All notable changes to Voxflow are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.0.0] — 2025-XX-XX

### Added
- Global hotkey `AltGr + ;` using `keyboard` library (Windows scan-code level)
- In-memory audio capture via `sounddevice` (no temporary files)
- Groq Whisper `whisper-large-v3` for speech-to-text (French)
- Groq `llama-3.3-70b-versatile` for LLM post-processing
- Context-aware dictation: reads selected text before processing
- Clipboard-based text injection (`Ctrl+V`) for reliable Unicode support
- `.env` configuration via `python-dotenv`
- Background pipeline worker thread (non-blocking hotkey response)
