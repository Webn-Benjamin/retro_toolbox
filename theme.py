"""theme.py — Fresh Green : blanc + gradients verts, design moderne."""
import model

# ── Palette Fresh Green (thème clair) ─────────────────────────────────
_LIGHT = {
    "BG":       "#f4fbf7",
    "BG_DARK":  "#e8f5ed",
    "SURFACE":  "#ffffff",
    "SURFACE2": "#f0faf4",
    "BORDER":   "#c8e6d0",
    "BORDER2":  "#a8d4b8",
    "TEXT":     "#0d2318",
    "SUBTEXT":  "#2e6648",
    "HINT":     "#74b08a",
}

# ── Palette sombre (dark mode) ─────────────────────────────────────────
_DARK = {
    "BG":       "#0d1610",
    "BG_DARK":  "#080f0a",
    "SURFACE":  "#111c14",
    "SURFACE2": "#162318",
    "BORDER":   "#1e3024",
    "BORDER2":  "#274034",
    "TEXT":     "#d4edd8",
    "SUBTEXT":  "#5a9068",
    "HINT":     "#3a6044",
}

# ── Commun aux deux thèmes ─────────────────────────────────────────────
_COMMON = {
    "ORANGE":   "#00b86e",   # accent principal (vert)
    "ORANGE_L": "#26cc87",   # hover
    "ORANGE_D": "#009958",   # pressed
    "GREEN":    "#00b86e",
    "RED":      "#e53935",
    "BLUE":     "#1e88e5",
    "GOLD":     "#f59520",
    "GRAD1":    "#00b86e",   # début gradient
    "GRAD2":    "#00968a",   # fin gradient
}


def _load_palette():
    dark = model.load_config().get("dark_theme", False)
    p    = _DARK if dark else _LIGHT
    return {**p, **_COMMON}


def _gradient(p):
    return (f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {p['GRAD1']},stop:1 {p['GRAD2']})")

def _gradient_v(p):
    return (f"qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 {p['GRAD1']},stop:1 {p['GRAD2']})")


def apply(palette: dict):
    import sys
    mod = sys.modules[__name__]
    for k, v in palette.items():
        setattr(mod, k, v)
    mod.QSS = _make_qss(palette)


def _make_qss(p: dict) -> str:
    grad  = _gradient(p)
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

/* ── Tooltips ───────────────────────────────── */
QToolTip {{
    background-color: {p['TEXT']};
    color: {p['SURFACE']};
    border: none;
    padding: 4px 8px;
    border-radius: 4px;
}}

/* ── Boutons génériques ─────────────────────── */
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

/* ── Boutons accent (gradient vert) ─────────── */
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
    background: {_gradient_v(p)};
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

/* ── Navbar principale ──────────────────────── */
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

/* ── Cards ──────────────────────────────────── */
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

/* ── Inputs ─────────────────────────────────── */
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

/* ── Scrollbars ─────────────────────────────── */
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

/* ── Sliders ────────────────────────────────── */
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

/* ── Dialogs ────────────────────────────────── */
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


# ── Init ──────────────────────────────────────────────────────────────
_p       = _load_palette()
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
