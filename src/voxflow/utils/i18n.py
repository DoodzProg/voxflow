"""
src/voxflow/utils/i18n.py

Lightweight two-language (EN / FR) internationalisation module.

All user-visible strings live in :data:`_STRINGS`.  Call :func:`tr` anywhere in
the codebase to get the translation for the current ``UI_LANGUAGE`` setting.
Adding a new language requires only:
  1. Adding the new language code to every entry in ``_STRINGS``.
  2. Adding the combo option in :mod:`~voxflow.ui.pages.general`.

Language codes follow ISO 639-1 (``"en"``, ``"fr"``).
Default language: ``"en"`` (English).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# String table
# ---------------------------------------------------------------------------

#: ``key → {lang_code → translated_string}``
_STRINGS: dict[str, dict[str, str]] = {

    # ── Navigation (sidebar) ────────────────────────────────────────────────
    "nav.home":     {"en": "Home",     "fr": "Accueil"},
    "nav.settings": {"en": "Settings", "fr": "Paramètres"},
    "nav.api":      {"en": "API Groq", "fr": "API Groq"},
    "nav.audio":    {"en": "Audio",    "fr": "Audio"},
    "nav.about":    {"en": "About",    "fr": "À propos"},

    # ── Sidebar misc ────────────────────────────────────────────────────────
    "sidebar.quit":        {"en": "  Close Voxflow",  "fr": "  Fermer Voxflow"},
    "sidebar.status.init": {"en": "Initializing…",    "fr": "Initialisation…"},

    # ── Home page ───────────────────────────────────────────────────────────
    "home.title":                {"en": "Dashboard",    "fr": "Tableau de bord"},
    "home.stat.words.label":     {"en": "Words today",  "fr": "Dictés aujourd'hui"},
    "home.stat.time.label":      {"en": "Recording time",  "fr": "Temps de dictée"},
    "home.stat.wpm.label":       {"en": "Avg. speed",   "fr": "Vitesse moyenne"},
    "home.stat.sessions.label":  {"en": "Sessions",     "fr": "Sessions complètes"},
    "home.stat.words.unit":      {"en": "words",        "fr": "mots"},
    "home.stat.wpm.unit":        {"en": "WPM",          "fr": "MPM"},
    "home.section.shortcuts":    {"en": "Active shortcuts",  "fr": "Raccourcis actifs"},
    "home.section.activity":     {"en": "RECENT ACTIVITY",   "fr": "ACTIVITÉ RÉCENTE"},
    "home.btn.clear":            {"en": "Reset",              "fr": "Réinitialiser"},
    "home.empty":   {
        "en": "No dictation yet — let's get started!",
        "fr": "Aucune dictée pour l'instant — lancez-vous !",
    },
    "home.shortcut.dictate": {"en": "Simple dictation",      "fr": "Dictée simple"},
    "home.shortcut.context": {
        "en": "Context instructions",
        "fr": "Instructions avec contexte",
    },
    "home.shortcut.hold": {
        "en": "Hold to speak, release to transcribe",
        "fr": "Maintenez pour parler, relâchez pour transcrire",
    },
    "home.shortcut.toggle": {
        "en": "Press to start, press again to transcribe",
        "fr": "Appuyez pour démarrer, ré-appuyez pour transcrire",
    },

    # ── General / Settings page ─────────────────────────────────────────────
    "general.title":             {"en": "Settings",             "fr": "Paramètres"},
    "general.section.hotkeys":   {"en": "Keyboard shortcuts",   "fr": "Raccourci clavier"},
    "general.hk.desc": {
        "en": "Click a button below, then press your key combination.",
        "fr": "Cliquez sur un bouton ci-dessous, puis appuyez sur votre combinaison.",
    },
    "general.hk.dictate":    {"en": "Simple dictation",       "fr": "Dictée simple"},
    "general.hk.context":    {
        "en": "Context instructions",
        "fr": "Instructions avec contexte",
    },
    "general.hk.mode":       {"en": "Trigger mode",           "fr": "Mode de déclenchement"},
    "general.hk.mode.hold":  {"en": "Hold (Push-to-Talk)",    "fr": "Maintien (Push-to-Talk)"},
    "general.hk.mode.toggle":{"en": "Press (Toggle)",         "fr": "Appui simple (Toggle)"},

    "general.section.behaviour":   {"en": "Behaviour",          "fr": "Comportement"},
    "general.startup.label":       {"en": "Launch at startup",   "fr": "Démarrage automatique"},
    "general.startup.desc":        {
        "en": "Start Voxflow when Windows starts",
        "fr": "Lancer Voxflow au démarrage de Windows",
    },
    "general.sound.label":         {"en": "Confirmation sound",  "fr": "Son de confirmation"},
    "general.sound.desc":          {
        "en": "Play a chime at the start and end of dictation",
        "fr": "Jouer un son au début et à la fin de la dictée",
    },
    "general.overlay.label":       {"en": "Dictation overlay",   "fr": "Bulle de dictée"},
    "general.overlay.desc":        {
        "en": "Show the floating indicator during recording",
        "fr": "Afficher l'indicateur flottant pendant l'enregistrement",
    },

    "general.section.language":    {"en": "Language & Region",   "fr": "Langue & Région"},
    "general.lang.dictation.label":{"en": "Dictation language",  "fr": "Langue de dictée"},
    "general.lang.dictation.desc": {
        "en": "Main language used for transcription",
        "fr": "Langue principale utilisée pour la transcription",
    },
    "general.lang.ui.label":       {"en": "Interface language",  "fr": "Langue de l'interface"},
    "general.lang.ui.desc":        {
        "en": "Voxflow display language",
        "fr": "Langue d'affichage de Voxflow",
    },

    # ── API page ─────────────────────────────────────────────────────────────
    "api.title":   {"en": "Groq API Key",   "fr": "Clé API Groq"},
    "api.banner":  {
        "en": "Your key is stored locally in your user profile.",
        "fr": "Votre clé est stockée localement dans votre profil.",
    },
    "api.section":       {"en": "Configuration",  "fr": "Configuration"},
    "api.key.label":     {"en": "Groq API Key",   "fr": "Clé API Groq"},
    "api.btn.verify":    {"en": "Verify key",     "fr": "Vérifier la clé"},
    "api.btn.save":      {"en": "Save",           "fr": "Sauvegarder"},
    "api.verify.empty":    {"en": "Key is empty!",  "fr": "Clé vide !"},
    "api.verify.checking": {"en": "Checking…",      "fr": "Vérification…"},
    "api.verify.valid":    {"en": "Key is valid!",  "fr": "Clé valide !"},
    "api.verify.invalid":  {"en": "Invalid key",    "fr": "Clé invalide"},
    "api.verify.error.title": {
        "en": "Verification error",
        "fr": "Erreur de vérification",
    },
    "api.verify.error.msg": {
        "en": "The API key was rejected by Groq.\n\nDetails: {exc}",
        "fr": "La clé API a été rejetée par Groq.\n\nDétail : {exc}",
    },
    "api.save.done": {"en": "Saved!", "fr": "Sauvegardé !"},

    # ── Audio page ───────────────────────────────────────────────────────────
    "audio.title":          {"en": "Audio",               "fr": "Audio"},
    "audio.section.input":  {"en": "Input device",        "fr": "Périphérique d'entrée"},
    "audio.mic.label":      {"en": "Microphone",          "fr": "Microphone"},
    "audio.mic.desc":       {
        "en": "Audio source used for dictation",
        "fr": "Source audio utilisée pour la dictée",
    },
    "audio.mic.none":       {
        "en": "No microphone detected",
        "fr": "Aucun microphone détecté",
    },
    "audio.test.label":     {"en": "Audio Test",          "fr": "Test Audio"},
    "audio.test.desc":      {
        "en": "Hear your voice with a short delay (0.5 s)",
        "fr": "Écoutez votre retour vocal avec un léger décalage (0.5 s)",
    },
    "audio.test.start":     {"en": "Test microphone",     "fr": "Tester le micro"},
    "audio.test.stop":      {
        "en": "Stop test (0.5 s delay)",
        "fr": "Arrêter le test (retour 0.5 s)",
    },

    # ── About page ───────────────────────────────────────────────────────────
    "about.tagline": {
        "en": "Open-source voice dictation. Fast, private, free.",
        "fr": "Dictée vocale open-source. Rapide, privée, gratuite.",
    },
    "about.section.version":  {"en": "Version",      "fr": "Version"},
    "about.version.label":    {"en": "Current version", "fr": "Version actuelle"},
    "about.version.desc":     {
        "en": "Phase 4 — GUI & .exe",
        "fr": "Phase 4 — Interface graphique & .exe",
    },
    "about.env.label":        {"en": "Environment",  "fr": "Environnement"},
    "about.env.desc":         {
        "en": "Groq Whisper transcription engine",
        "fr": "Moteur de transcription Groq Whisper",
    },
    "about.section.links":    {"en": "Links",         "fr": "Liens"},
    "about.link.github":      {
        "en": "GitHub — Source code & releases",
        "fr": "GitHub — Code source et releases",
    },
    "about.link.bug":         {"en": "Report a bug",         "fr": "Signaler un bug"},
    "about.link.feature":     {"en": "Request a feature",    "fr": "Proposer une fonctionnalité"},
    "about.btn.update":       {"en": "Check for updates",    "fr": "Vérifier les mises à jour"},
    "about.update.checking":  {"en": "Checking…",            "fr": "Vérification…"},
    "about.update.available": {
        "en": "Update available: v{tag}",
        "fr": "Mise à jour disponible : v{tag}",
    },
    "about.update.uptodate":  {"en": "You are up to date.",   "fr": "Vous êtes à jour."},
    "about.update.noreleases":{"en": "No releases found yet.", "fr": "Aucune release disponible."},
    "about.update.error":     {"en": "Error {code}.",          "fr": "Erreur {code}."},
    "about.update.unreachable":{
        "en": "Could not reach GitHub.",
        "fr": "Impossible de contacter GitHub.",
    },

    # ── Engine status messages ───────────────────────────────────────────────
    "engine.recording":    {"en": "Recording…",           "fr": "Enregistrement…"},
    "engine.processing":   {"en": "Processing…",          "fr": "Traitement…"},
    "engine.cleaning":     {"en": "Cleaning up (LLM)…",   "fr": "Nettoyage (LLM)…"},
    "engine.ready":        {"en": "Ready to dictate",     "fr": "Prêt à dicter"},
    "engine.error":        {"en": "Error",                "fr": "Erreur"},
    "engine.error.conn":   {"en": "Connection error",     "fr": "Erreur de connexion"},
    "engine.error.nokey":  {
        "en": "API key missing. Go to the API Groq tab.",
        "fr": "Clé API manquante. Allez dans l'onglet API Groq.",
    },
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def tr(key: str) -> str:
    """Return the translation of *key* in the current UI language.

    Reads ``UI_LANGUAGE`` from :class:`~voxflow.utils.config.ConfigManager` on
    every call so language switches take effect immediately without requiring a
    restart.  Falls back to English if the current language or key is not found.

    Args:
        key: Dot-separated string key defined in :data:`_STRINGS`.

    Returns:
        The translated string, or *key* itself if no entry is found.
    """
    # Import here to avoid a module-level circular dependency in tests.
    from voxflow.utils.config import ConfigManager  # noqa: PLC0415

    lang = ConfigManager.get("UI_LANGUAGE", "en")
    entry = _STRINGS.get(key, {})
    return entry.get(lang) or entry.get("en") or key
