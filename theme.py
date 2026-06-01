"""theme.py — Palette claire / sombre + styles Qt."""

import model

# ── Palettes ───────────────────────────────────────────────

_LIGHT = {
    "BG":       "#e8dcc8",
    "BG_DARK":  "#d6c9b0",
    "SURFACE":  "#f5efe2",
    "SURFACE2": "#faf6ee",
    "BORDER":   "#c9b99a",
    "BORDER2":  "#b8a484",
    "TEXT":     "#2d241b",
    "SUBTEXT":  "#7a6a56",
    "HINT":     "#a89880",
}

_DARK = {
    "BG":       "#1e1e2e",
    "BG_DARK":  "#16161f",
    "SURFACE":  "#2a2a3e",
    "SURFACE2": "#32324a",
    "BORDER":   "#3a3a55",
    "BORDER2":  "#4a4a68",
    "TEXT":     "#e8dcc8",
    "SUBTEXT":  "#a89880",
    "HINT":     "#6a6a88",
}

_COMMON = {
    "ORANGE":   "#d9791f",
    "ORANGE_L": "#e8883a",
    "ORANGE_D": "#b8620f",
    "GREEN":    "#5e8020",
    "RED":      "#8c4038",
    "BLUE":     "#4e6e96",
    "GOLD":     "#c4952a",
}

# ── Chargement du thème actif ──────────────────────────────

def _load_palette():
    dark = model.load_config().get("dark_theme", False)
    p = _DARK if dark else _LIGHT
    return {**p, **_COMMON}

def apply(palette: dict):
    """Met à jour toutes les variables globales du module."""
    import sys
    mod = sys.modules[__name__]
    for k, v in palette.items():
        setattr(mod, k, v)
    # Regénérer le QSS
    mod.QSS = _make_qss(palette)

def _make_qss(p: dict) -> str:
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
    font-size: 9pt;
}}
QWidget {{
    background-color: transparent;
    color: {p['TEXT']};
    font-family: "Segoe UI";
    font-size: 9pt;
}}
QMainWindow > QWidget {{ background-color: {p['BG']}; }}
QDialog > QWidget    {{ background-color: {p['BG']}; }}
QScrollArea > QWidget > QWidget {{ background-color: {p['BG']}; }}
QDialog QLabel {{ background-color: transparent; color: {p['TEXT']}; }}
QDialog QPushButton {{
    background-color: {p['BG_DARK']}; color: {p['SUBTEXT']};
    border: 1px solid {p['BORDER']}; border-radius: 3px;
    padding: 5px 12px; font-weight: bold;
}}
QDialog QPushButton:hover {{ background-color: {p['BORDER']}; }}
QDialog QComboBox {{
    background-color: {p['SURFACE2']}; border: 1px solid {p['BORDER']};
    border-radius: 3px; padding: 4px 8px; color: {p['TEXT']};
}}
QDialog QComboBox QAbstractItemView {{
    background-color: {p['SURFACE']};
    selection-background-color: {p['ORANGE']};
    selection-color: white; color: {p['TEXT']};
}}
QDialog QLineEdit {{
    background-color: {p['SURFACE2']}; border: 1px solid {p['BORDER']};
    border-radius: 3px; padding: 5px 8px; color: {p['TEXT']};
}}
QDialog QFrame#card {{
    background-color: {p['SURFACE']}; border: 1px solid {p['BORDER']}; border-radius: 4px;
}}
QFrame#card {{
    background-color: {p['SURFACE']}; border: 1px solid {p['BORDER']}; border-radius: 4px;
}}
QFrame#card_dark {{
    background-color: {p['BG_DARK']}; border: 1px solid {p['BORDER']}; border-radius: 0px;
}}
QFrame#sep {{
    background-color: {p['BORDER']}; max-height: 1px; border: none;
}}
QPushButton {{
    background-color: {p['BG_DARK']}; color: {p['SUBTEXT']};
    border: 1px solid {p['BORDER']}; border-radius: 3px;
    padding: 5px 12px; font-weight: bold;
}}
QPushButton:hover {{ background-color: {p['BORDER']}; }}
QPushButton#btn_orange {{ background-color: {p['ORANGE']}; color: white; border: none; }}
QPushButton#btn_orange:hover {{ background-color: {p['ORANGE_L']}; }}
QPushButton#btn_green  {{ background-color: {p['GREEN']};  color: white; border: none; }}
QPushButton#btn_green:hover  {{ background-color: #6e9428; }}
QPushButton#btn_red    {{ background-color: {p['RED']};    color: white; border: none; }}
QPushButton#btn_red:hover    {{ background-color: #9e4840; }}
QPushButton#btn_blue   {{ background-color: {p['BLUE']};   color: white; border: none; }}
QPushButton#nav_active {{
    background-color: {p['SURFACE']}; color: {p['ORANGE']};
    border: none; border-top: 2px solid {p['ORANGE']};
    font-size: 7pt; font-weight: bold; padding: 4px 2px;
}}
QPushButton#nav_inactive {{
    background-color: {p['BG_DARK']}; color: {p['HINT']};
    border: none; font-size: 7pt; font-weight: bold; padding: 4px 2px;
}}
QPushButton#nav_inactive:hover {{ color: {p['SUBTEXT']}; }}
QLineEdit {{
    background-color: {p['SURFACE2']}; border: 1px solid {p['BORDER']};
    border-radius: 3px; padding: 5px 8px; color: {p['TEXT']};
}}
QLineEdit:focus {{ border-color: {p['ORANGE']}; }}
QSlider::groove:horizontal {{ background: {p['BG_DARK']}; height: 4px; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: {p['SURFACE']}; border: 1px solid {p['BORDER']};
    width: 16px; height: 16px; border-radius: 8px; margin: -6px 0;
}}
QSlider::sub-page:horizontal {{ background: {p['ORANGE']}; border-radius: 2px; }}
QScrollBar:vertical {{
    background: {p['BG_DARK']}; width: 6px; border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {p['BORDER2']}; border-radius: 3px; min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: {p['ORANGE']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QToolTip {{
    background-color: {p['TEXT']}; color: {p['SURFACE']};
    border: none; padding: 4px 8px; border-radius: 2px;
}}
QComboBox {{
    background-color: {p['SURFACE2']}; border: 1px solid {p['BORDER']};
    border-radius: 3px; padding: 4px 8px; color: {p['TEXT']};
}}
QComboBox QAbstractItemView {{
    background-color: {p['SURFACE']};
    selection-background-color: {p['ORANGE']};
    selection-color: white; border: 1px solid {p['BORDER']};
}}
"""

# ── Init au chargement ────────────────────────────────────

_p = _load_palette()
BG       = _p["BG"];      BG_DARK  = _p["BG_DARK"]
SURFACE  = _p["SURFACE"]; SURFACE2 = _p["SURFACE2"]
BORDER   = _p["BORDER"];  BORDER2  = _p["BORDER2"]
TEXT     = _p["TEXT"];    SUBTEXT  = _p["SUBTEXT"];  HINT = _p["HINT"]
ORANGE   = _p["ORANGE"];  ORANGE_L = _p["ORANGE_L"]; ORANGE_D = _p["ORANGE_D"]
GREEN    = _p["GREEN"];   RED      = _p["RED"]
BLUE     = _p["BLUE"];    GOLD     = _p["GOLD"]
QSS      = _make_qss(_p)


def sep(parent=None):
    from PySide6.QtWidgets import QFrame
    f = QFrame(parent)
    f.setObjectName("sep")
    f.setFrameShape(QFrame.Shape.HLine)
    f.setMaximumHeight(1)
    return f
