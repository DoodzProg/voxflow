"""
AcouZ - Open-source AI voice dictation
Copyright (c) 2025-2026 DoodzProg
Licensed under the MIT License

Centralised theme and styling module — single dark green theme.
All QSS helpers, colour constants and SVG icon paths live here so that the
rest of the UI layer never hard-codes visual values.
"""

from __future__ import annotations
from dataclasses import dataclass
from PySide6.QtGui import QColor, QPalette

_FONT = "'Segoe UI Variable', 'Segoe UI'"

# -- Logo SVG — A with Z-pulse crossbar --
# The A's horizontal bar is replaced by a green Z-shaped lightning bolt,
# fusing the letters A and Z into a single acoustic geometry.
LOGO_SVG: str = (
    '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">'
    '<defs>'
    '<linearGradient id="bgL" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0%"   stop-color="#1E2822"/>'
    '<stop offset="100%" stop-color="#121814"/>'
    '</linearGradient>'
    '</defs>'
    '<rect width="200" height="200" rx="44" fill="url(#bgL)"/>'
    # Left leg of A
    '<line x1="40" y1="164" x2="100" y2="36"'
    ' stroke="white" stroke-width="20"'
    ' stroke-linecap="round" stroke-linejoin="round"/>'
    # Right leg of A
    '<line x1="100" y1="36" x2="160" y2="164"'
    ' stroke="white" stroke-width="20"'
    ' stroke-linecap="round" stroke-linejoin="round"/>'
    # Z-pulse crossbar (green lightning bolt connecting both legs at ~60% height)
    '<polyline points="66,108 88,88 112,128 134,108"'
    ' fill="none" stroke="#1DB954" stroke-width="9"'
    ' stroke-linecap="round" stroke-linejoin="round"/>'
    '</svg>'
)

@dataclass(frozen=True)
class Theme:
    bg_deep:       str
    bg_sidebar:    str
    bg_card:       str
    bg_hover:      str
    border:        str
    accent:        str
    accent_light:  str
    accent_purple: str   # dark green tint for active nav bg
    danger:        str
    text_1:        str
    text_2:        str
    text_3:        str

# Single theme — dark green (Spotify/VS Code inspired)
DARK = Theme(
    bg_deep       = "#121814",   # ~VS Code #1E1E1E, green-tinted
    bg_sidebar    = "#181F1B",   # ~Spotify sidebar #121212 lightened
    bg_card       = "#1E2822",   # card surface, clearly distinct from bg
    bg_hover      = "#263530",   # hover state
    border        = "#2E3D37",   # subtle separator
    accent        = "#1DB954",
    accent_light  = "#1ED760",
    accent_purple = "#1A4530",   # dark green tint for active nav bg
    danger        = "#EF4444",
    text_1        = "#E8EDE9",
    text_2        = "#8FA89C",
    text_3        = "#526560",
)

# Alias — no light theme, kept so imports don't break
LIGHT = DARK

ICONS: dict[str, str] = {
    "home":     '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
                '<polyline points="9 22 9 12 15 12 15 22"/>',
    "settings": '<circle cx="12" cy="12" r="3"/>'
                '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06'
                'a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09'
                'A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83'
                'l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09'
                'A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83'
                'l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09'
                'a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83'
                'l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09'
                'a1.65 1.65 0 0 0-1.51 1z"/>',
    "key":      '<path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0'
                'L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/>',
    "mic":      '<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>'
                '<path d="M19 10v2a7 7 0 0 1-14 0v-2"/>'
                '<line x1="12" y1="19" x2="12" y2="23"/>'
                '<line x1="8" y1="23" x2="16" y2="23"/>',
    "volume":   '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>'
                '<path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>',
    "info":     '<circle cx="12" cy="12" r="10"/>'
                '<line x1="12" y1="8" x2="12" y2="12"/>'
                '<line x1="12" y1="16" x2="12.01" y2="16"/>',
    "eye":      '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>'
                '<circle cx="12" cy="12" r="3"/>',
    "eye_off":  '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8'
                'a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4'
                'c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07'
                'a3 3 0 1 1-4.24-4.24"/>'
                '<line x1="1" y1="1" x2="23" y2="23"/>',
    "keyboard": '<rect x="2" y="4" width="20" height="16" rx="2" ry="2"/>'
                '<path d="M6 8h.01M10 8h.01M14 8h.01M18 8h.01'
                'M8 12h.01M12 12h.01M16 12h.01M7 16h10"/>',
    "zap":      '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "check":    '<polyline points="20 6 9 17 4 12"/>',
    "clock":    '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "star":     '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 '
                '12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    "x_mark":   '<line x1="18" y1="6" x2="6" y2="18"/>'
                '<line x1="6" y1="6" x2="18" y2="18"/>',
    "bug":      '<rect x="8" y="6" width="8" height="14" rx="4"/>'
                '<line x1="12" y1="6" x2="12" y2="3"/>'
                '<path d="M20 8l-3 2M4 8l3 2M20 16l-3-2M4 16l3-2"/>',
    "arrow_r":  '<line x1="5" y1="12" x2="19" y2="12"/>'
                '<polyline points="12 5 19 12 12 19"/>',
    "link":     '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>'
                '<path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    "refresh":  '<polyline points="23 4 23 10 17 10"/>'
                '<path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>',
    "sun":      '<circle cx="12" cy="12" r="5"/>'
                '<line x1="12" y1="1" x2="12" y2="3"/>'
                '<line x1="12" y1="21" x2="12" y2="23"/>'
                '<line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>'
                '<line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>'
                '<line x1="1" y1="12" x2="3" y2="12"/>'
                '<line x1="21" y1="12" x2="23" y2="12"/>'
                '<line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>'
                '<line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>',
    "moon":     '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>',
}

def get_qss(is_dark: bool = True) -> str:
    t = DARK
    return f"""
    QWidget, QLabel, QPushButton, QComboBox, QLineEdit {{
        font-family: 'Segoe UI Variable', 'Segoe UI';
    }}

    QScrollBar:vertical {{ background: transparent; width: 5px; margin: 0; }}
    QScrollBar::handle:vertical {{ background: {t.text_3}; border-radius: 3px; min-height: 24px; }}
    QScrollBar::handle:vertical:hover {{ background: {t.text_2}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

    QToolTip {{ background: {t.bg_card}; color: {t.text_1}; border-radius: 6px;
               padding: 4px 8px; font-size: 12px; border: 1px solid {t.border}; }}
    QMainWindow, QWidget {{ background: {t.bg_deep}; color: {t.text_1}; }}
    QScrollArea {{ background: transparent; border: none; }}

    QMenu {{ background: {t.bg_card}; color: {t.text_1}; border-radius: 8px; padding: 4px;
             font-size: 13px; border: 1px solid {t.border}; }}
    QMenu::item {{ padding: 6px 20px; border-radius: 4px; }}
    QMenu::item:selected {{ background: {t.accent}22; color: {t.text_1}; }}

    QComboBox {{
        background-color: {t.bg_hover}; border: 1px solid {t.border};
        border-radius: 8px; padding: 6px 36px 6px 12px;
        color: {t.text_1}; font-size: 13px; min-height: 32px;
    }}
    QComboBox:hover {{ border: 1px solid {t.accent}; background: {t.bg_card}; }}
    QComboBox:focus  {{ border: 1px solid {t.accent}; outline: none; }}
    QComboBox::drop-down {{ border: none; width: 32px; }}
    QComboBox::down-arrow {{ image: none; }}
    QComboBox QAbstractItemView {{
        background-color: {t.bg_card}; border: 1px solid {t.border};
        border-radius: 8px; color: {t.text_1}; padding: 4px;
        selection-background-color: {t.accent}33;
        selection-color: {t.text_1}; outline: none;
    }}
    QAbstractItemView::item {{ padding: 6px 12px; border-radius: 6px; min-height: 28px; }}
    QAbstractItemView::item:hover {{ background: {t.bg_hover}; }}
    """

def get_palette(is_dark: bool = True) -> QPalette:
    t = DARK
    pal = QPalette()
    pal.setColor(QPalette.Window,          QColor(t.bg_deep))
    pal.setColor(QPalette.WindowText,      QColor(t.text_1))
    pal.setColor(QPalette.Base,            QColor(t.bg_card))
    pal.setColor(QPalette.AlternateBase,   QColor(t.bg_hover))
    pal.setColor(QPalette.Text,            QColor(t.text_1))
    pal.setColor(QPalette.Button,          QColor(t.bg_card))
    pal.setColor(QPalette.ButtonText,      QColor(t.text_1))
    pal.setColor(QPalette.Highlight,       QColor(t.accent))
    pal.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    pal.setColor(QPalette.PlaceholderText, QColor(t.text_3))
    return pal

def pill_badge_qss(color: str = "") -> str:
    _ACCENT = "#1DB954"
    return (
        f"QLabel {{ background: #1A1DB954; color: {_ACCENT}; "
        f"border: 1px solid #401DB954; border-radius: 9px; "
        f"padding: 3px 10px; font-size: 11px; font-weight: 600; "
        f"font-family: 'Segoe UI'; }}"
    )

def nav_button_qss(active: bool, t: Theme) -> str:
    bg  = "#221DB954" if active else "transparent"
    hov = "#331DB954" if active else "#0AE0E6E2"
    return (
        f"QPushButton {{ background: {bg}; border: none; border-radius: 8px; }} "
        f"QPushButton:hover {{ background: {hov}; }}"
    )

def nav_label_style(active: bool, t: Theme) -> str:
    color  = t.accent if active else t.text_2
    weight = "600" if active else "400"
    return (
        f"color: {color}; font-size: 14px; font-weight: {weight}; "
        f"font-family: {_FONT}; background: transparent;"
    )

def card_qss(t: Theme) -> str:
    return f"QFrame {{ background: {t.bg_card}; border-radius: 12px; }}"

def hline_qss(t: Theme) -> str:
    return f"background: {t.text_3.replace('#', '#44')}; border: none; max-height: 1px; margin: 0 20px;"

def page_title_style(t: Theme) -> str:
    return (
        f"color: {t.text_1}; font-size: 24px; font-weight: 700; "
        f"font-family: {_FONT}; background: transparent;"
    )

def section_title_style(t: Theme) -> str:
    return (
        f"color: {t.text_3}; font-size: 11px; font-weight: 700; "
        f"letter-spacing: 1.8px; font-family: {_FONT}; background: transparent;"
    )

def setting_label_style(t: Theme) -> str:
    return (
        f"color: {t.text_1}; font-size: 14px; font-weight: 600; "
        f"font-family: {_FONT}; background: transparent;"
    )

def setting_desc_style(t: Theme) -> str:
    return (
        f"color: {t.text_2}; font-size: 12px; "
        f"font-family: {_FONT}; background: transparent;"
    )

def btn_primary_qss(t: Theme) -> str:
    return (
        f"QPushButton {{ background: {t.accent}; color: #090B0A; border: none; "
        f"border-radius: 8px; font-size: 13px; font-weight: 600; "
        f"font-family: 'Segoe UI'; padding: 0 20px; }} "
        f"QPushButton:hover {{ background: {t.accent_light}; }} "
        f"QPushButton:pressed {{ background: {t.accent}; }}"
    )

def btn_ghost_qss(t: Theme) -> str:
    return (
        f"QPushButton {{ background: transparent; color: {t.text_2}; border-radius: 8px; "
        f"font-size: 13px; font-family: 'Segoe UI'; padding: 0 16px; }} "
        f"QPushButton:hover {{ color: {t.accent_light}; background: #121DB954; }}"
    )

def btn_outlined_qss(t: Theme) -> str:
    return (
        f"QPushButton {{ background: transparent; color: {t.text_1}; "
        f"border: 1px solid {t.border}; border-radius: 8px; "
        f"font-size: 13px; font-family: 'Segoe UI'; padding: 6px 16px; }} "
        f"QPushButton:hover {{ color: {t.accent_light}; border-color: {t.accent_light}; "
        f"background: #121DB954; }}"
    )

def line_edit_qss(t: Theme) -> str:
    return (
        f"QLineEdit {{ background: {t.bg_hover}; color: {t.text_1}; border-radius: 9px; "
        f"padding: 0 14px; font-size: 13px; font-family: 'Consolas', 'Courier New'; "
        f"border: 1px solid {t.border}; }} "
        f"QLineEdit:focus {{ background: {t.bg_card}; border: 1px solid {t.accent}; }}"
    )

def eye_btn_qss(t: Theme) -> str:
    return (
        f"QPushButton {{ background: {t.bg_hover}; border-radius: 9px; }} "
        f"QPushButton:hover {{ background: {t.bg_card}; }}"
    )

def hotkey_idle_qss(t: Theme) -> str:
    return (
        f"QPushButton {{ background: {t.bg_card}; border-radius: 10px; "
        f"border: 1px solid {t.border}; }} "
        f"QPushButton:hover {{ background: {t.bg_deep}; }}"
    )

def hotkey_listening_qss(t: Theme) -> str:
    return (
        f"QPushButton {{ background: {t.bg_card}; "
        f"border: 1px dashed {t.danger}; border-radius: 10px; }}"
    )

def hotkey_chip_style(t: Theme) -> str:
    rgb = t.accent.lstrip("#")
    return (
        f"color: {t.text_1}; background: #18{rgb}; "
        f"border: 1px solid #44{rgb}; "
        f"border-radius: 5px; padding: 2px 8px; "
        f"font-size: 11px; font-weight: 600; font-family: {_FONT};"
    )

def shortcut_chip_style(t: Theme) -> str:
    return (
        f"color: {t.accent}; background: #221DB954; "
        f"border-radius: 6px; padding: 4px 12px; "
        f"font-size: 12px; font-weight: 600; font-family: 'Segoe UI';"
    )

def stat_card_qss(t: Theme) -> str:
    return (
        f"QFrame {{ background: {t.bg_card}; border-radius: 12px; }} "
        f"QFrame:hover {{ background: {t.bg_hover}; }}"
    )

def status_bar_qss(t: Theme) -> str:
    return f"QFrame {{ background: {t.bg_card}; border-radius: 8px; }}"

def api_banner_qss(t: Theme) -> str:
    return (
        f"QFrame {{ background: {t.bg_card}; "
        f"border-left: 3px solid {t.accent}; border-radius: 10px; }}"
    )

def about_logo_qss(t: Theme) -> str:
    return (
        f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1, "
        f"stop:0 {t.accent}, stop:1 #0A3D1E); border-radius: 14px;"
    )

def shortcut_card_qss(t: Theme) -> str:
    return (
        f"QFrame {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, "
        f"stop:0 #221DB954, stop:1 {t.bg_card}); border-radius: 12px; }}"
    )

def theme_toggle_qss(t: Theme) -> str:
    """Kept for API compatibility — theme toggle removed."""
    return ""

def theme_icon_btn_qss(t: Theme) -> str:
    """Kept for API compatibility — theme toggle removed."""
    return (
        f"QPushButton {{ background: transparent; border: none; border-radius: 6px; }} "
        f"QPushButton:hover {{ background: {t.bg_hover}; }}"
    )

def sidebar_qss(t: Theme) -> str:
    return f"background: {t.bg_sidebar};"

def pages_qss(t: Theme) -> str:
    return f"background: {t.bg_deep};"
