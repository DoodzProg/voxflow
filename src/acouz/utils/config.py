"""
AcouZ - Open-source AI voice dictation
Copyright (c) 2025-2026 DoodzProg
Licensed under the MIT License

Configuration management for the AcouZ application.

All user preferences and secrets are stored in a ``.env`` file at the project
root.  :class:`ConfigManager` provides a thin, thread-safe facade over
``python-dotenv`` so the rest of the application never deals with raw
environment variables or file paths directly.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv, set_key

# ------------------------------------------------------------------
# Path resolution
# ------------------------------------------------------------------

#: Absolute path to this file.
_UTILS_DIR: Path = Path(__file__).parent

#: ``src/acouz/`` package directory.
_PKG_DIR: Path = _UTILS_DIR.parent

#: ``src/`` directory.
_SRC_DIR: Path = _PKG_DIR.parent

#: Project root (contains ``pyproject.toml``, ``.env``, ``README.md`` ...).
ROOT_DIR: Path = _SRC_DIR.parent

#: Path to the persistent configuration file.
ENV_PATH: Path = ROOT_DIR / ".env"


# ------------------------------------------------------------------
# ConfigManager
# ------------------------------------------------------------------

class ConfigManager:
    """Static helper class for reading and writing user configuration.

    Configuration is persisted in a ``.env`` file and exposed as OS environment
    variables so that any third-party library relying on ``os.getenv`` (e.g.
    the Groq SDK) picks up the values automatically.

    All methods are ``@staticmethod`` — there is no instance state.

    Example::

        ConfigManager.initialize()
        api_key = ConfigManager.get("GROQ_API_KEY")
        ConfigManager.set("MICROPHONE", "Casque (Realtek Audio)")
    """

    @staticmethod
    def initialize() -> None:
        """Load environment variables from ``.env`` and create the file if missing.

        Should be called once at application startup before any :meth:`get`
        or :meth:`set` calls are made.
        """
        if not ENV_PATH.exists():
            ENV_PATH.touch()
        load_dotenv(dotenv_path=ENV_PATH)

    @staticmethod
    def get(key: str, default: str = "") -> str:
        """Return the value for *key*, or *default* if it is not set.

        Args:
            key:     Environment variable name (e.g. ``"GROQ_API_KEY"``).
            default: Fallback value when the key is absent (default ``""``).

        Returns:
            The string value associated with *key*, or *default*.
        """
        return os.getenv(key, default)

    @staticmethod
    def set(key: str, value: str) -> None:
        """Persist *value* for *key* in ``.env`` and update the live environment.

        Writing to ``.env`` ensures the value survives an application restart.
        Updating ``os.environ`` makes the change visible to the current process
        immediately, without requiring a reload.

        Args:
            key:   Environment variable name.
            value: String value to store.

        Raises:
            OSError: If the ``.env`` file cannot be created or written.
        """
        if not ENV_PATH.exists():
            ENV_PATH.touch()

        set_key(
            dotenv_path=str(ENV_PATH),
            key_to_set=key,
            value_to_set=value,
            quote_mode="never",
        )
        os.environ[key] = value
