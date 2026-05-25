"""theme.py — Palette et styles Qt."""

BG        = "#e8dcc8"
BG_DARK   = "#d6c9b0"
SURFACE   = "#f5efe2"
SURFACE2  = "#faf6ee"
BORDER    = "#c9b99a"
BORDER2   = "#b8a484"
TEXT      = "#2d241b"
SUBTEXT   = "#7a6a56"
HINT      = "#a89880"
ORANGE    = "#d9791f"
ORANGE_L  = "#e8883a"
ORANGE_D  = "#b8620f"
GREEN     = "#5e8020"
RED       = "#8c4038"
BLUE      = "#4e6e96"
GOLD      = "#c4952a"

# QSS minimal — on laisse les widgets hériter sans forcer de fond
QSS = f"""
QMainWindow {{
    background-color: {BG};
    color: {TEXT};
    font-family: "Segoe UI";
    font-size: 9pt;
}}

QDialog {{
    background-color: {BG};
    color: {TEXT};
    font-family: "Segoe UI";
    font-size: 9pt;
}}

QWidget {{
    background-color: transparent;
    color: {TEXT};
    font-family: "Segoe UI";
    font-size: 9pt;
}}

QMainWindow > QWidget {{
    background-color: {BG};
}}

QDialog > QWidget {{
    background-color: {BG};
}}

QScrollArea > QWidget > QWidget {{
    background-color: {BG};
}}

QDialog QLabel {{
    background-color: transparent;
    color: {TEXT};
}}

QDialog QPushButton {{
    background-color: {BG_DARK};
    color: {SUBTEXT};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 5px 12px;
    font-weight: bold;
}}

QDialog QPushButton:hover {{
    background-color: {BORDER};
}}

QDialog QComboBox {{
    background-color: {SURFACE2};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 4px 8px;
    color: {TEXT};
}}

QDialog QComboBox QAbstractItemView {{
    background-color: {SURFACE};
    selection-background-color: {ORANGE};
    selection-color: white;
    color: {TEXT};
}}

QDialog QLineEdit {{
    background-color: {SURFACE2};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 5px 8px;
    color: {TEXT};
}}

QDialog QFrame#card {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 4px;
}}

/* Cartes */
QFrame#card {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 4px;
}}

QFrame#card_dark {{
    background-color: {BG_DARK};
    border: 1px solid {BORDER};
    border-radius: 0px;
}}

/* Séparateur */
QFrame#sep {{
    background-color: {BORDER};
    max-height: 1px;
    border: none;
}}

/* Boutons */
QPushButton {{
    background-color: {BG_DARK};
    color: {SUBTEXT};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 5px 12px;
    font-weight: bold;
}}
QPushButton:hover {{ background-color: {BORDER}; }}

QPushButton#btn_orange {{
    background-color: {ORANGE};
    color: white;
    border: none;
}}
QPushButton#btn_orange:hover {{ background-color: {ORANGE_L}; }}

QPushButton#btn_green {{
    background-color: {GREEN};
    color: white;
    border: none;
}}
QPushButton#btn_green:hover {{ background-color: #6e9428; }}

QPushButton#btn_red {{
    background-color: {RED};
    color: white;
    border: none;
}}
QPushButton#btn_red:hover {{ background-color: #9e4840; }}

QPushButton#btn_blue {{
    background-color: {BLUE};
    color: white;
    border: none;
}}

QPushButton#nav_active {{
    background-color: {SURFACE};
    color: {ORANGE};
    border: none;
    border-top: 2px solid {ORANGE};
    font-size: 7pt;
    font-weight: bold;
    padding: 4px 2px;
}}

QPushButton#nav_inactive {{
    background-color: {BG_DARK};
    color: {HINT};
    border: none;
    font-size: 7pt;
    font-weight: bold;
    padding: 4px 2px;
}}
QPushButton#nav_inactive:hover {{ color: {SUBTEXT}; }}

/* Inputs */
QLineEdit {{
    background-color: {SURFACE2};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 5px 8px;
    color: {TEXT};
}}
QLineEdit:focus {{ border-color: {ORANGE}; }}

/* Slider */
QSlider::groove:horizontal {{
    background: {BG_DARK};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: white;
    border: 1px solid {BORDER};
    width: 16px;
    height: 16px;
    border-radius: 8px;
    margin: -6px 0;
}}
QSlider::sub-page:horizontal {{
    background: {ORANGE};
    border-radius: 2px;
}}

/* ScrollBar */
QScrollBar:vertical {{
    background: {BG_DARK};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER2};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: {ORANGE}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QToolTip {{
    background-color: {TEXT};
    color: {SURFACE};
    border: none;
    padding: 4px 8px;
    border-radius: 2px;
}}

QComboBox {{
    background-color: {SURFACE2};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 4px 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {SURFACE};
    selection-background-color: {ORANGE};
    selection-color: white;
    border: 1px solid {BORDER};
}}
"""


def sep(parent=None):
    from PySide6.QtWidgets import QFrame
    f = QFrame(parent)
    f.setObjectName("sep")
    f.setFrameShape(QFrame.Shape.HLine)
    f.setMaximumHeight(1)
    return f
