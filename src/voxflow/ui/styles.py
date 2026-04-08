"""
src/voxflow/ui/styles.py
Centralised theme and styling module for the Voxflow PySide6 UI.
"""

from __future__ import annotations
from dataclasses import dataclass
from PySide6.QtGui import QColor, QPalette

# Primary font stack: Segoe UI Variable (Windows 11 variable font) with
# Segoe UI as fallback for Windows 10 and earlier.
_FONT = "'Segoe UI Variable', 'Segoe UI'"

# ── Application logo (SVG, embedded so it works inside PyInstaller bundles) ──
# The gradient id uses a unique name ("bgL") to avoid conflicts when multiple
# instances of the SVG are rendered on the same page.
LOGO_SVG: str = (
    '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">'
    '<defs>'
    '<linearGradient id="bgL" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0%"   stop-color="#7C6FEB"/>'
    '<stop offset="100%" stop-color="#5B4FCF"/>'
    '</linearGradient>'
    '</defs>'
    # Rounded-square background
    '<rect width="200" height="200" rx="44" fill="url(#bgL)"/>'
    # Bold V — the mic-housing side arms
    '<path d="M 34 52 L 100 158 L 166 52"'
    ' stroke="white" stroke-width="22"'
    ' stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
    # Top bar that closes the mic housing
    '<rect x="23" y="40" width="154" height="20" rx="10" fill="white"/>'
    # Tapered grille lines (opacity 0.55)
    '<line x1="61"  y1="82"  x2="139" y2="82"'
    ' stroke="white" stroke-width="3" stroke-linecap="round" opacity="0.55"/>'
    '<line x1="72"  y1="104" x2="128" y2="104"'
    ' stroke="white" stroke-width="3" stroke-linecap="round" opacity="0.55"/>'
    '<line x1="84"  y1="126" x2="116" y2="126"'
    ' stroke="white" stroke-width="3" stroke-linecap="round" opacity="0.55"/>'
    '</svg>'
)

@dataclass(frozen=True)
class Theme:
    bg_deep:    str
    bg_sidebar: str
    bg_card:    str
    bg_hover:   str
    border:     str
    accent:        str   
    accent_light:  str   
    accent_purple: str   
    danger: str   
    text_1: str   
    text_2: str   
    text_3: str   

DARK = Theme(
    bg_deep       = "#0F0E17",
    bg_sidebar    = "#13111F",
    bg_card       = "#13111F",
    bg_hover      = "#1E1C2E",
    border        = "#2D2B45",
    accent        = "#7C6FEB",
    accent_light  = "#C4BFFA",
    accent_purple = "#5B4FCF", 
    danger        = "#F87171",
    text_1        = "#E8E6F8",
    text_2        = "#B0AECB",
    text_3        = "#6B6A85",
)

LIGHT = Theme(
    bg_deep       = "#F8F7FF",
    bg_sidebar    = "#FFFFFF",
    bg_card       = "#FFFFFF",
    bg_hover      = "#F0EFFE",
    border        = "#E2E0F8",
    accent        = "#7C6FEB",
    accent_light  = "#5B4FCF",
    accent_purple = "#EDE9FD", 
    danger        = "#991B1B",
    text_1        = "#1A1830",
    text_2        = "#4A4869",
    text_3        = "#7B7A96",
)

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

def _t(is_dark: bool) -> Theme:
    return DARK if is_dark else LIGHT

def get_qss(is_dark: bool) -> str:
    t = _t(is_dark)
    return f"""
    /* Global font — Segoe UI Variable (Windows 11) with Segoe UI fallback */
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

    /* ComboBox — custom chevron is drawn by StyledComboBox.paintEvent */
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

def get_palette(is_dark: bool) -> QPalette:
    t = _t(is_dark)
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

# ─────────────────────────────────────────────────────────────
#  Toutes les transparences ont été corrigées pour utiliser le format #AARRGGBB
# ─────────────────────────────────────────────────────────────

def pill_badge_qss(color: str) -> str:
    # Remplace "#" par "#26" au début de la couleur pour faire du ARGB valide dans Qt !
    bg = color.replace('#', '#26')
    return (
        f"QLabel {{ background: {bg}; color: {color}; border-radius: 9px; "
        f"padding: 4px 10px; font-size: 11px; font-weight: 600; font-family: 'Segoe UI'; }}"
    )

def nav_button_qss(active: bool, t: Theme) -> str:
    bg  = t.accent_purple.replace('#', '#22') if active else "transparent"
    hov = t.accent_purple.replace('#', '#33') if active else t.text_1.replace('#', '#0A')
    return f"QPushButton {{ background: {bg}; border: none; border-radius: 8px; }} QPushButton:hover {{ background: {hov}; }}"

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
        f"QPushButton {{ background: {t.accent}; color: white; border: none; "
        f"border-radius: 8px; font-size: 13px; font-weight: 600; "
        f"font-family: 'Segoe UI'; padding: 0 20px; }} "
        f"QPushButton:hover {{ background: {t.accent_light}; }} "
        f"QPushButton:pressed {{ background: {t.accent.replace('#', '#CC')}; }}"
    )

def btn_ghost_qss(t: Theme) -> str:
    bg_hover = t.accent.replace('#', '#12')
    return (
        f"QPushButton {{ background: transparent; color: {t.text_2}; border-radius: 8px; "
        f"font-size: 13px; font-family: 'Segoe UI'; padding: 0 16px; }} "
        f"QPushButton:hover {{ color: {t.accent_light}; background: {bg_hover}; }}"
    )

def line_edit_qss(t: Theme) -> str:
    return (
        f"QLineEdit {{ background: {t.bg_hover}; color: {t.text_1}; border-radius: 9px; "
        f"padding: 0 14px; font-size: 13px; font-family: 'Consolas', 'Courier New'; border: 1px solid {t.border}; }} "
        f"QLineEdit:focus {{ background: {t.bg_card}; border: 1px solid {t.accent}; }}"
    )

def eye_btn_qss(t: Theme) -> str:
    return f"QPushButton {{ background: {t.bg_hover}; border-radius: 9px; }} QPushButton:hover {{ background: {t.bg_card}; }}"

def hotkey_idle_qss(t: Theme) -> str:
    # Hover only changes the background — the border stays unchanged so no
    # unexpected colour (e.g. green from a mis-parsed AARRGGBB value) appears.
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
    # Flat 2D chip: subtle accent tint + accent border.
    # Qt 8-digit hex is AARRGGBB — alpha must be the FIRST two digits.
    # Appending alpha after the RGB (e.g. "#7C6FEB18") mis-parses as a
    # different colour entirely; prepending it gives the correct result.
    rgb = t.accent.lstrip("#")
    return (
        f"color: {t.text_1}; background: #18{rgb}; "
        f"border: 1px solid #44{rgb}; "
        f"border-radius: 5px; padding: 2px 8px; "
        f"font-size: 11px; font-weight: 600; font-family: {_FONT};"
    )

def shortcut_chip_style(t: Theme) -> str:
    bg = t.accent_purple.replace('#', '#33')
    return f"color: {t.accent}; background: {bg}; border-radius: 6px; padding: 4px 12px; font-size: 12px; font-weight: 600; font-family: 'Segoe UI';"

def stat_card_qss(t: Theme) -> str:
    return f"QFrame {{ background: {t.bg_card}; border-radius: 12px; }} QFrame:hover {{ background: {t.bg_hover}; }}"

def status_bar_qss(t: Theme) -> str:
    return f"QFrame {{ background: {t.bg_card}; border-radius: 8px; }}"

def api_banner_qss(t: Theme) -> str:
    return f"QFrame {{ background: {t.bg_card}; border-left: 3px solid {t.accent}; border-radius: 10px; }}"

def about_logo_qss(t: Theme) -> str:
    # Use a fixed deep-purple as the second gradient stop so the logo looks
    # equally vivid in both DARK and LIGHT modes.
    return (
        f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1, "
        f"stop:0 {t.accent}, stop:1 #5B4FCF); border-radius: 14px;"
    )

def shortcut_card_qss(t: Theme) -> str:
    bg = t.accent_purple.replace('#', '#22')
    return f"QFrame {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {bg}, stop:1 {t.bg_card}); border-radius: 12px; }}"

def theme_toggle_qss(t: Theme) -> str:
    bg_hover = t.accent_purple.replace('#', '#33')
    return (
        f"QPushButton {{ background: {t.bg_hover}; color: {t.text_2}; "
        f"border-radius: 8px; font-size: 12px; font-family: 'Segoe UI'; "
        f"padding: 0 12px; text-align: left; }} "
        f"QPushButton:hover {{ background: {bg_hover}; color: {t.accent}; }}"
    )

def theme_icon_btn_qss(t: Theme) -> str:
    """QSS for the compact sun/moon toggle button in the title bar."""
    return (
        f"QPushButton {{ background: transparent; border: none; border-radius: 6px; }} "
        f"QPushButton:hover {{ background: {t.bg_hover}; }}"
    )

def sidebar_qss(t: Theme) -> str:
    return f"background: {t.bg_sidebar};"

def pages_qss(t: Theme) -> str:
    return f"background: {t.bg_deep};"