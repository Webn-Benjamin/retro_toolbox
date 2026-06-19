"""theme.py — Système de thèmes avec support thèmes personnalisés."""
import model

# ── Thèmes intégrés ────────────────────────────────────────────────────

BUILTIN_THEMES = {

    "clair": {
        "BG":       "#f4fbf7",
        "BG_DARK":  "#e8f5ed",
        "SURFACE":  "#ffffff",
        "SURFACE2": "#f0faf4",
        "BORDER":   "#c8e6d0",
        "BORDER2":  "#a8d4b8",
        "TEXT":     "#0d2318",
        "SUBTEXT":  "#2e6648",
        "HINT":     "#74b08a",
        "ORANGE":   "#00b86e",
        "ORANGE_L": "#26cc87",
        "ORANGE_D": "#009958",
        "GREEN":    "#00b86e",
        "RED":      "#e53935",
        "BLUE":     "#1e88e5",
        "GOLD":     "#f59520",
        "GRAD1":    "#00b86e",
        "GRAD2":    "#00968a",
    },

    "sombre": {
        "BG":       "#0d1610",
        "BG_DARK":  "#080f0a",
        "SURFACE":  "#111c14",
        "SURFACE2": "#162318",
        "BORDER":   "#1e3024",
        "BORDER2":  "#274034",
        "TEXT":     "#d4edd8",
        "SUBTEXT":  "#5a9068",
        "HINT":     "#3a6044",
        "ORANGE":   "#00b86e",
        "ORANGE_L": "#26cc87",
        "ORANGE_D": "#009958",
        "GREEN":    "#00b86e",
        "RED":      "#e53935",
        "BLUE":     "#1e88e5",
        "GOLD":     "#f59520",
        "GRAD1":    "#00b86e",
        "GRAD2":    "#00968a",
    },

    "retro": {
        "BG":       "#F8F2E6",
        "BG_DARK":  "#EDE4CC",
        "SURFACE":  "#F8F2E6",
        "SURFACE2": "#F0E8D4",
        "BORDER":   "#D0C4A0",
        "BORDER2":  "#BCA878",
        "TEXT":     "#2C1C08",
        "SUBTEXT":  "#4A3818",
        "HINT":     "#6A5030",
        "ORANGE":   "#5A3A18",
        "ORANGE_L": "#7A5A38",
        "ORANGE_D": "#3A2008",
        "GREEN":    "#5A7A28",
        "RED":      "#B03020",
        "BLUE":     "#2860A0",
        "GOLD":     "#C88010",
        "GRAD1":    "#5A3A18",
        "GRAD2":    "#3A2008",
    },

    "retro_dark": {
        "BG":       "#121008",
        "BG_DARK":  "#1C1610",
        "SURFACE":  "#1C1610",
        "SURFACE2": "#241E14",
        "BORDER":   "#2C2218",
        "BORDER2":  "#3C2E20",
        "TEXT":     "#ECD8A8",
        "SUBTEXT":  "#C8A870",
        "HINT":     "#7A5A38",
        "ORANGE":   "#C8873A",
        "ORANGE_L": "#E0A050",
        "ORANGE_D": "#A06820",
        "GREEN":    "#6A8A38",
        "RED":      "#D07060",
        "BLUE":     "#5880B0",
        "GOLD":     "#D09030",
        "GRAD1":    "#5A3A18",
        "GRAD2":    "#3A2008",
    },
}

BUILTIN_LABELS = {
    "clair":      "☀️  Clair",
    "sombre":     "🌙  Sombre",
    "retro":      "🏺  Rétro",
    "retro_dark": "🏺  Rétro sombre",
}


def _gradient(p):
    return (f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {p['GRAD1']},stop:1 {p['GRAD2']})")

def _gradient_v(p):
    return (f"qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 {p['GRAD1']},stop:1 {p['GRAD2']})")


def _make_qss(p: dict) -> str:
    grad   = _gradient(p)
    grad_v = _gradient_v(p)
    return f"""
QMainWindow {{
    background-color: {p['BG']};
    color: {p['TEXT']};
    font-family: "Segoe UI";
    font-size: 9pt;
}}
QDialog {{
    background-color: {p['BG']};
    color: {p['TEXT']};
    font-family: "Segoe UI";
}}
QWidget {{
    background-color: transparent;
    color: {p['TEXT']};
    font-family: "Segoe UI";
    font-size: 9pt;
}}
QMainWindow > QWidget {{ background-color: {p['BG']}; }}
QDialog     > QWidget {{ background-color: {p['BG']}; }}
QScrollArea > QWidget > QWidget {{ background-color: {p['BG']}; }}

QToolTip {{
    background-color: {p['TEXT']};
    color: {p['SURFACE']};
    border: none;
    padding: 4px 8px;
    border-radius: 4px;
}}

QPushButton {{
    background-color: {p['BG_DARK']};
    color: {p['SUBTEXT']};
    border: 1px solid {p['BORDER']};
    border-radius: 6px;
    padding: 5px 12px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {p['BORDER']};
    color: {p['TEXT']};
}}
QPushButton:pressed {{
    background-color: {p['BORDER2']};
}}

QPushButton#btn_orange,
QPushButton#btn_accent {{
    background: {grad};
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 700;
}}
QPushButton#btn_orange:hover,
QPushButton#btn_accent:hover {{
    background: {grad_v};
}}
QPushButton#btn_green {{
    background: {grad};
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 700;
}}
QPushButton#btn_red {{
    background-color: {p['RED']};
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 700;
}}
QPushButton#btn_blue {{
    background-color: {p['BLUE']};
    color: white;
    border: none;
    border-radius: 8px;
}}

QPushButton#nav_active {{
    background-color: {p['SURFACE']};
    color: {p['ORANGE']};
    border: none;
    border-top: 2px solid {p['ORANGE']};
    font-size: 7pt;
    font-weight: 700;
    padding: 4px 2px;
}}
QPushButton#nav_inactive {{
    background-color: {p['BG_DARK']};
    color: {p['HINT']};
    border: none;
    font-size: 7pt;
    font-weight: 700;
    padding: 4px 2px;
}}
QPushButton#nav_inactive:hover {{ color: {p['SUBTEXT']}; }}

QFrame#card {{
    background-color: {p['SURFACE']};
    border: 1px solid {p['BORDER']};
    border-radius: 8px;
}}
QFrame#card_dark {{
    background-color: {p['BG_DARK']};
    border: 1px solid {p['BORDER']};
    border-radius: 8px;
}}
QFrame#sep {{
    background-color: {p['BORDER']};
    max-height: 1px;
    border: none;
}}

QLineEdit {{
    background-color: {p['SURFACE']};
    border: 1px solid {p['BORDER']};
    border-radius: 6px;
    padding: 5px 10px;
    color: {p['TEXT']};
}}
QLineEdit:focus {{
    border: 1px solid {p['ORANGE']};
}}
QComboBox {{
    background-color: {p['SURFACE']};
    border: 1px solid {p['BORDER']};
    border-radius: 6px;
    padding: 4px 8px;
    color: {p['TEXT']};
}}
QComboBox QAbstractItemView {{
    background-color: {p['SURFACE']};
    selection-background-color: {p['ORANGE']};
    selection-color: white;
    border: 1px solid {p['BORDER']};
    border-radius: 6px;
}}
QSpinBox {{
    background-color: {p['SURFACE']};
    border: 1px solid {p['BORDER']};
    border-radius: 6px;
    padding: 3px 6px;
    color: {p['TEXT']};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 5px;
    border-radius: 6px;
}}
QScrollBar::handle:vertical {{
    background: {p['BORDER2']};
    border-radius: 6px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: {p['ORANGE']}; }}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{ height: 0; }}

QSlider::groove:horizontal {{
    background: {p['BG_DARK']};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {p['SURFACE']};
    border: 2px solid {p['ORANGE']};
    width: 14px;
    height: 14px;
    border-radius: 7px;
    margin: -5px 0;
}}
QSlider::sub-page:horizontal {{
    background: {grad};
    border-radius: 2px;
}}

QDialog QLabel {{ background-color: transparent; color: {p['TEXT']}; }}
QDialog QPushButton {{
    background-color: {p['BG_DARK']};
    color: {p['SUBTEXT']};
    border: 1px solid {p['BORDER']};
    border-radius: 6px;
    padding: 5px 12px;
    font-weight: 600;
}}
QDialog QPushButton:hover {{ background-color: {p['BORDER']}; }}
"""


def get_active_palette() -> dict:
    """Retourne la palette active (builtin ou custom)."""
    cfg = model.load_config()
    theme_name = cfg.get("theme_name", "")
    # Thème personnalisé
    if theme_name.startswith("custom:"):
        custom_name = theme_name[7:]
        customs = cfg.get("custom_themes", {})
        if custom_name in customs:
            return customs[custom_name]
    # Thème builtin
    if theme_name in BUILTIN_THEMES:
        return BUILTIN_THEMES[theme_name]
    # Compatibilité ancienne config
    dark = cfg.get("dark_theme", False)
    return BUILTIN_THEMES["sombre" if dark else "clair"]


# ── Init au démarrage ──────────────────────────────────────────────────
_p       = get_active_palette()
BG       = _p["BG"];      BG_DARK  = _p["BG_DARK"]
SURFACE  = _p["SURFACE"]; SURFACE2 = _p["SURFACE2"]
BORDER   = _p["BORDER"];  BORDER2  = _p["BORDER2"]
TEXT     = _p["TEXT"];    SUBTEXT  = _p["SUBTEXT"];  HINT = _p["HINT"]
ORANGE   = _p["ORANGE"];  ORANGE_L = _p["ORANGE_L"]; ORANGE_D = _p["ORANGE_D"]
GREEN    = _p["GREEN"];   RED      = _p["RED"]
BLUE     = _p["BLUE"];    GOLD     = _p["GOLD"]
GRAD1    = _p["GRAD1"];   GRAD2    = _p["GRAD2"]
QSS      = _make_qss(_p)

GRADIENT = (f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {GRAD1},stop:1 {GRAD2})")


def sep(parent=None):
    from PySide6.QtWidgets import QFrame
    f = QFrame(parent)
    f.setObjectName("sep")
    f.setFrameShape(QFrame.Shape.HLine)
    f.setMaximumHeight(1)
    return f
