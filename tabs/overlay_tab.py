"""tabs/overlay_tab.py — Overlay de marqueurs sur l'écran."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QSlider, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, QTimer, QPoint, QSize, QRect
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QScreen

import model, theme

T = theme
CFG_KEY = "overlay_config"

try:
    import keyboard
    KEYBOARD_OK = True
except Exception:
    KEYBOARD_OK = False


# ── OverlayWindow ──────────────────────────────────────────

class OverlayWindow(QWidget):
    """Fenêtre transparente plein écran qui affiche les marqueurs."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput  # transparent aux clics par défaut
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

        # Couvrir tout l'écran principal
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        self._markers: list[dict] = []  # {x, y, color, size}
        self._visible = False

    def set_markers(self, markers):
        self._markers = markers
        self.update()

    def show_overlay(self):
        self._visible = True
        self.show()
        self.raise_()

    def hide_overlay(self):
        self._visible = False
        self.hide()

    def paintEvent(self, e):
        if not self._markers: return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for m in self._markers:
            color = QColor(m['color'])
            color.setAlpha(200)
            p.setBrush(QBrush(color))
            border = QColor(m['color']).darker(150)
            border.setAlpha(220)
            p.setPen(QPen(border, 2))
            r = m['size'] // 2
            p.drawEllipse(m['x'] - r, m['y'] - r, m['size'], m['size'])
        p.end()


# ── OverlayTab ─────────────────────────────────────────────

class OverlayTab(QWidget):

    COLORS = [
        ("#e05555", "Rouge"),
        ("#e08c30", "Orange"),
        ("#d4c832", "Jaune"),
        ("#5cb85c", "Vert"),
        ("#5bc0de", "Bleu clair"),
        ("#4e6e96", "Bleu"),
        ("#9b59b6", "Violet"),
        ("#ffffff", "Blanc"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        cfg = model.load_config().get(CFG_KEY, {})
        self._maps: dict         = cfg.get("maps", {"Map 1": []})
        self._current_map: str   = cfg.get("current_map", "Map 1")
        self._active_color: str  = cfg.get("active_color", "#e05555")
        self._active_size: int   = cfg.get("active_size", 24)
        self._sc_add: str        = cfg.get("sc_add", "")
        self._sc_undo: str       = cfg.get("sc_undo", "")
        self._sc_reset: str      = cfg.get("sc_reset", "")
        self._sc_map: str        = cfg.get("sc_map", "")
        self._overlay_on: bool   = cfg.get("overlay_on", True)

        self._overlay = OverlayWindow()
        self._build()
        self._register_hotkeys()
        self._refresh_overlay()

    # ── Build ──────────────────────────────────────────────

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        # ── Toggle overlay ─────────────────────────────────
        top = QHBoxLayout()
        title = QLabel("🎯 Dots")
        title.setStyleSheet(f"font-size:11pt;font-weight:bold;color:{T.TEXT};background:transparent;")
        top.addWidget(title, 1)

        self._toggle_btn = QPushButton("● Actif")
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setChecked(self._overlay_on)
        self._toggle_btn.setFixedHeight(30)
        self._toggle_btn.setStyleSheet(self._toggle_style(self._overlay_on))
        self._toggle_btn.clicked.connect(self._toggle_overlay)
        top.addWidget(self._toggle_btn)
        lay.addLayout(top)

        lay.addWidget(_sep())

        # ── Map courante ───────────────────────────────────
        # Nom de la map + navigation
        nav_row = QHBoxLayout(); nav_row.setSpacing(4)

        btn_prev = QPushButton("◀")
        btn_prev.setFixedSize(26, 26)
        btn_prev.setToolTip("Map précédente")
        btn_prev.setStyleSheet(_nav_btn_ss())
        btn_prev.clicked.connect(lambda: self._cycle_map(-1))

        self._map_lbl = QLabel(self._current_map)
        self._map_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._map_lbl.setStyleSheet(
            f"color:{T.ORANGE};font-size:10pt;font-weight:bold;background:transparent;")

        btn_next = QPushButton("▶")
        btn_next.setFixedSize(26, 26)
        btn_next.setToolTip("Map suivante")
        btn_next.setStyleSheet(_nav_btn_ss())
        btn_next.clicked.connect(lambda: self._cycle_map(1))

        nav_row.addWidget(btn_prev)
        nav_row.addWidget(self._map_lbl, 1)
        nav_row.addWidget(btn_next)
        lay.addLayout(nav_row)

        # Boutons gérer les maps sur une ligne séparée
        mgr_row = QHBoxLayout(); mgr_row.setSpacing(4)

        btn_add_map = QPushButton("＋  Nouvelle map")
        btn_add_map.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};"
            f"border:1px solid {T.BORDER};border-radius:3px;"
            f"padding:4px 8px;font-size:7.5pt;font-weight:bold;}}"
            f"QPushButton:hover{{border-color:{T.GREEN};color:{T.GREEN};}}")
        btn_add_map.clicked.connect(self._add_map)

        btn_del_map = QPushButton("✕  Supprimer")
        btn_del_map.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};"
            f"border:1px solid {T.BORDER};border-radius:3px;"
            f"padding:4px 8px;font-size:7.5pt;font-weight:bold;}}"
            f"QPushButton:hover{{border-color:{T.RED};color:{T.RED};}}")
        btn_del_map.clicked.connect(self._del_map)

        mgr_row.addWidget(btn_add_map, 1)
        mgr_row.addWidget(btn_del_map, 1)
        lay.addLayout(mgr_row)

        lay.addWidget(_sep())

        # ── Couleur ────────────────────────────────────────
        lay.addWidget(_lbl("Couleur du marqueur", T.HINT, "8pt", bold=True))
        color_row = QHBoxLayout(); color_row.setSpacing(5)
        self._color_btns = {}
        for color, name in self.COLORS:
            b = QPushButton()
            b.setFixedSize(28, 28)
            b.setToolTip(name)
            active = color == self._active_color
            b.setStyleSheet(self._color_btn_ss(color, active))
            b.clicked.connect(lambda _, c=color: self._set_color(c))
            color_row.addWidget(b)
            self._color_btns[color] = b
        color_row.addStretch()
        lay.addLayout(color_row)

        # ── Taille ────────────────────────────────────────
        lay.addWidget(_lbl("Taille du marqueur", T.HINT, "8pt", bold=True))
        size_row = QHBoxLayout(); size_row.setSpacing(8)
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(10, 80)
        self._slider.setValue(self._active_size)
        self._slider.setStyleSheet(
            f"QSlider::groove:horizontal{{height:4px;background:{T.BORDER};border-radius:2px;}}"
            f"QSlider::handle:horizontal{{width:14px;height:14px;margin:-5px 0;"
            f"background:{T.ORANGE};border-radius:7px;}}"
            f"QSlider::sub-page:horizontal{{background:{T.ORANGE};border-radius:2px;}}")
        self._size_lbl = QLabel(f"{self._active_size}px")
        self._size_lbl.setStyleSheet(
            f"color:{T.ORANGE};font-size:9pt;font-weight:bold;background:transparent;")
        self._size_lbl.setFixedWidth(36)
        self._slider.valueChanged.connect(self._on_size_change)
        size_row.addWidget(self._slider, 1)
        size_row.addWidget(self._size_lbl)
        lay.addLayout(size_row)

        # Prévisualisation
        self._preview = _ColorDot(self._active_color, self._active_size)
        preview_row = QHBoxLayout()
        preview_row.addStretch()
        preview_row.addWidget(self._preview)
        preview_row.addStretch()
        lay.addLayout(preview_row)

        lay.addWidget(_sep())

        # ── Actions ────────────────────────────────────────
        lay.addWidget(_lbl("Actions", T.HINT, "8pt", bold=True))

        actions_row = QHBoxLayout(); actions_row.setSpacing(6)
        btn_undo = QPushButton("↩ Dernier")
        btn_undo.setStyleSheet(_action_btn_ss(T.BG_DARK, T.SUBTEXT, T.ORANGE))
        btn_undo.clicked.connect(self._undo_last)

        btn_reset = QPushButton("✕ Reset map")
        btn_reset.setStyleSheet(_action_btn_ss(T.BG_DARK, T.SUBTEXT, T.RED))
        btn_reset.clicked.connect(self._reset_map)

        btn_reset_all = QPushButton("✕✕ Tout reset")
        btn_reset_all.setStyleSheet(_action_btn_ss(T.BG_DARK, T.SUBTEXT, T.RED))
        btn_reset_all.clicked.connect(self._reset_all)

        actions_row.addWidget(btn_undo)
        actions_row.addWidget(btn_reset)
        actions_row.addWidget(btn_reset_all)
        lay.addLayout(actions_row)

        # ── Compteur de marqueurs ──────────────────────────
        self._count_lbl = _lbl("", T.HINT, "8pt")
        self._count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._count_lbl)

        lay.addWidget(_sep())

        # ── Raccourcis ─────────────────────────────────────
        lay.addWidget(_lbl("Raccourcis clavier", T.HINT, "8pt", bold=True))
        self._sc_rows = {}
        shortcuts = [
            ("sc_add",   "Placer un marqueur"),
            ("sc_undo",  "Annuler le dernier"),
            ("sc_reset", "Reset la map"),
            ("sc_map",   "Changer de map →"),
        ]
        for key, label in shortcuts:
            row = self._build_sc_row(key, label)
            lay.addLayout(row)

        self._refresh_count()

    def _build_sc_row(self, key, label):
        row = QHBoxLayout(); row.setSpacing(6)
        lbl = _lbl(label, T.SUBTEXT, "8pt")
        lbl.setFixedWidth(130)
        row.addWidget(lbl)
        from PySide6.QtWidgets import QLineEdit
        inp = QLineEdit(getattr(self, f"_{key}") or "")
        inp.setPlaceholderText("Ex: ctrl+shift+a")
        inp.setStyleSheet(
            f"QLineEdit{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:3px;padding:3px 6px;color:{T.TEXT};font-size:8pt;}}"
            f"QLineEdit:focus{{border-color:{T.ORANGE};}}")
        btn = QPushButton("✔"); btn.setFixedWidth(26)
        btn.setStyleSheet(
            f"QPushButton{{background:{T.GREEN};color:white;border:none;"
            f"border-radius:3px;padding:3px;font-size:9pt;}}"
            f"QPushButton:hover{{background:#6e9428;}}")
        btn.clicked.connect(lambda _, k=key, i=inp: self._save_sc(k, i.text().strip()))
        row.addWidget(inp, 1); row.addWidget(btn)
        self._sc_rows[key] = inp
        return row

    # ── Overlay ────────────────────────────────────────────

    def _toggle_overlay(self, checked):
        self._overlay_on = checked
        self._toggle_btn.setText("● Actif" if checked else "○ Inactif")
        self._toggle_btn.setStyleSheet(self._toggle_style(checked))
        if checked:
            self._overlay.show_overlay()
        else:
            self._overlay.hide_overlay()
        self._save()

    def _toggle_style(self, on):
        if on:
            return (f"QPushButton{{background:{T.GREEN};color:white;border:none;"
                    f"border-radius:3px;padding:4px 12px;font-size:9pt;font-weight:bold;}}"
                    f"QPushButton:hover{{background:#6e9428;}}")
        return (f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
                f"border:1px solid {T.BORDER};border-radius:3px;"
                f"padding:4px 12px;font-size:9pt;font-weight:bold;}}"
                f"QPushButton:hover{{border-color:{T.ORANGE};}}")

    def _refresh_overlay(self):
        markers = self._maps.get(self._current_map, [])
        self._overlay.set_markers(markers)
        if self._overlay_on:
            self._overlay.show_overlay()

    # ── Maps ───────────────────────────────────────────────

    def _cycle_map(self, direction):
        keys = list(self._maps.keys())
        if not keys: return
        idx = keys.index(self._current_map) if self._current_map in keys else 0
        idx = (idx + direction) % len(keys)
        self._current_map = keys[idx]
        self._map_lbl.setText(self._current_map)
        self._refresh_overlay()
        self._refresh_count()
        self._save()

    def _add_map(self):
        keys = list(self._maps.keys())
        name = f"Map {len(keys) + 1}"
        i = 1
        while name in self._maps:
            name = f"Map {len(keys) + i}"
            i += 1
        self._maps[name] = []
        self._current_map = name
        self._map_lbl.setText(name)
        self._refresh_overlay()
        self._refresh_count()
        self._save()
        self._fit()

    def _del_map(self):
        if len(self._maps) <= 1: return
        del self._maps[self._current_map]
        self._current_map = list(self._maps.keys())[0]
        self._map_lbl.setText(self._current_map)
        self._refresh_overlay()
        self._refresh_count()
        self._save()

    # ── Marqueurs ──────────────────────────────────────────

    def _place_marker(self):
        from PySide6.QtGui import QCursor
        pos = QCursor.pos()
        marker = {
            "x": pos.x(), "y": pos.y(),
            "color": self._active_color,
            "size": self._active_size
        }
        if self._current_map not in self._maps:
            self._maps[self._current_map] = []
        self._maps[self._current_map].append(marker)
        self._refresh_overlay()
        self._refresh_count()
        self._save()

    def _undo_last(self):
        markers = self._maps.get(self._current_map, [])
        if markers:
            markers.pop()
            self._refresh_overlay()
            self._refresh_count()
            self._save()

    def _reset_map(self):
        self._maps[self._current_map] = []
        self._refresh_overlay()
        self._refresh_count()
        self._save()

    def _reset_all(self):
        for k in self._maps:
            self._maps[k] = []
        self._refresh_overlay()
        self._refresh_count()
        self._save()

    def _refresh_count(self):
        n = len(self._maps.get(self._current_map, []))
        total = sum(len(v) for v in self._maps.values())
        self._count_lbl.setText(
            f"{n} marqueur{'s' if n>1 else ''} sur cette map · {total} au total")

    # ── Couleur / Taille ───────────────────────────────────

    def _set_color(self, color):
        self._active_color = color
        for c, b in self._color_btns.items():
            b.setStyleSheet(self._color_btn_ss(c, c == color))
        self._preview.set_color(color)
        self._save()

    def _on_size_change(self, val):
        self._active_size = val
        self._size_lbl.setText(f"{val}px")
        self._preview.set_size(val)
        self._save()

    def _color_btn_ss(self, color, active):
        border = color if active else T.BORDER
        ring = f"border:3px solid {T.TEXT};" if active else f"border:2px solid {border};"
        return (f"QPushButton{{background:{color};{ring}"
                f"border-radius:4px;}}"
                f"QPushButton:hover{{border:3px solid {T.TEXT};}}")

    # ── Raccourcis ─────────────────────────────────────────

    def _save_sc(self, key, value):
        setattr(self, f"_{key}", value)
        self._save()
        self._register_hotkeys()

    def _register_hotkeys(self):
        if not KEYBOARD_OK: return
        try: keyboard.unhook_all_hotkeys()
        except Exception: pass
        pairs = [
            (self._sc_add,   self._place_marker),
            (self._sc_undo,  self._undo_last),
            (self._sc_reset, self._reset_map),
            (self._sc_map,   lambda: self._cycle_map(1)),
        ]
        for sc, fn in pairs:
            if sc:
                try: keyboard.add_hotkey(sc, fn, suppress=False)
                except Exception: pass

    # ── Save / Fit ─────────────────────────────────────────

    def _save(self):
        model.save_config({CFG_KEY: {
            "maps":         self._maps,
            "current_map":  self._current_map,
            "active_color": self._active_color,
            "active_size":  self._active_size,
            "sc_add":       self._sc_add,
            "sc_undo":      self._sc_undo,
            "sc_reset":     self._sc_reset,
            "sc_map":       self._sc_map,
            "overlay_on":   self._overlay_on,
        }})

    def _fit(self):
        w = self
        while w:
            w.updateGeometry()
            w = w.parentWidget()
        root = self.window()
        if not root: return
        root.setMinimumHeight(0)
        root.setMaximumHeight(16777215)
        root.adjustSize()

    def sizeHint(self):
        lay = self.layout()
        if not lay: return QSize(330, 400)
        h = lay.contentsMargins().top() + lay.contentsMargins().bottom()
        for i in range(lay.count()):
            item = lay.itemAt(i)
            if not item: continue
            w = item.widget()
            if w and w.isVisible():
                h += w.sizeHint().height() + lay.spacing()
            elif item.layout():
                h += 30 + lay.spacing()
        return QSize(330, h)

    def closeEvent(self, e):
        self._overlay.hide()
        super().closeEvent(e)


# ── Helpers ────────────────────────────────────────────────

class _ColorDot(QWidget):
    """Prévisualisation du marqueur."""
    def __init__(self, color, size, parent=None):
        super().__init__(parent)
        self._color = color
        self._size = size
        self.setFixedHeight(50)

    def set_color(self, c): self._color = c; self.update()
    def set_size(self, s): self._size = s; self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(self._color)
        color.setAlpha(200)
        p.setBrush(QBrush(color))
        p.setPen(QPen(QColor(self._color).darker(150), 2))
        s = min(self._size, 44)
        x = (self.width() - s) // 2
        y = (self.height() - s) // 2
        p.drawEllipse(x, y, s, s)
        p.end()


def _sep():
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"color:{T.BORDER};max-height:1px;")
    return f

def _lbl(text, color=None, size="9pt", bold=False):
    l = QLabel(text)
    ss = f"background:transparent;font-size:{size};"
    if color: ss += f"color:{color};"
    if bold:  ss += "font-weight:bold;"
    l.setStyleSheet(ss)
    return l

def _nav_btn_ss():
    return (f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};"
            f"border:1px solid {T.BORDER};border-radius:3px;font-size:9pt;}}"
            f"QPushButton:hover{{border-color:{T.ORANGE};color:{T.ORANGE};}}")

def _action_btn_ss(bg, fg, hov):
    return (f"QPushButton{{background:{bg};color:{fg};"
            f"border:1px solid {T.BORDER};border-radius:3px;"
            f"padding:5px 8px;font-size:8pt;font-weight:bold;}}"
            f"QPushButton:hover{{color:{hov};border-color:{hov};}}")
