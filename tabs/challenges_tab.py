"""tabs/challenges_tab.py — Challenges PySide6, panneaux inline."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QStackedWidget, QLineEdit, QApplication, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QMimeData, QPoint, QTimer
from PySide6.QtGui import QPixmap, QColor, QDrag
import sys
from pathlib import Path
import model, theme
from spell_data import SPELLS, CLASS_COLORS, CLASS_FOLDER

T = theme  # raccourci


def resource_path(rel):
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / rel
    return Path(__file__).parent.parent / rel


def _btn(text, color, hover, callback, w=None, pad="9px 0"):
    b = QPushButton(text)
    b.setStyleSheet(
        f"QPushButton{{background:{color};color:white;border:none;border-radius:4px;"
        f"padding:{pad};font-weight:bold;font-size:9pt;}}"
        f"QPushButton:hover{{background:{hover};}}")
    if w: b.setFixedWidth(w)
    b.clicked.connect(callback)
    return b


def _sep():
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"color:{T.BORDER};max-height:1px;")
    return f


# ── SpellCard ──────────────────────────────────────────────

class SpellCard(QLabel):
    toggled_signal = Signal(str, bool)

    def __init__(self, spell, cls_key, profile_key, grid, parent=None):
        super().__init__(parent)
        self.spell = spell; self.cls_key = cls_key
        self.profile_key = profile_key; self._grid = grid
        self._greyed = False; self._dragging = False
        self._press_timer = None
        self.setFixedSize(55, 55)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(spell['nom'])
        self.setAcceptDrops(True)
        self._load()

    def _load(self):
        path = resource_path(f"{CLASS_FOLDER.get(self.cls_key,'spells/cra')}/{self.spell['img']}.png")
        pix = QPixmap(str(path))
        if pix.isNull():
            pix = QPixmap(55, 55); pix.fill(QColor(T.BG_DARK))
        if self._greyed:
            img = pix.toImage()
            for y in range(img.height()):
                for x in range(img.width()):
                    c = img.pixelColor(x, y)
                    g = int(c.red()*0.3+c.green()*0.59+c.blue()*0.11)
                    c.setRgb(g//2, g//2, g//2, int(c.alpha()*0.65))
                    img.setPixelColor(x, y, c)
            pix = QPixmap.fromImage(img)
        self.setPixmap(pix.scaled(55, 55, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation))

    def set_greyed(self, v): self._greyed = v; self._load()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self._press_timer = QTimer()
            self._press_timer.setSingleShot(True)
            self._press_timer.timeout.connect(lambda: setattr(self, '_dragging', True))
            self._press_timer.start(200)

    def mouseReleaseEvent(self, e):
        if self._press_timer and self._press_timer.isActive():
            self._press_timer.stop()
        if not self._dragging:
            self._greyed = not self._greyed; self._load()
            self.toggled_signal.emit(self.spell['nom'], self._greyed)
        self._dragging = False

    def mouseMoveEvent(self, e):
        if self._dragging:
            drag = QDrag(self)
            mime = QMimeData(); mime.setText(self.spell['nom'])
            drag.setMimeData(mime)
            drag.setPixmap(self.pixmap().scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio,
                                                Qt.TransformationMode.SmoothTransformation))
            drag.setHotSpot(QPoint(22, 22))
            drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, e):
        if e.mimeData().hasText():
            e.acceptProposedAction()
            self.setStyleSheet(f"QLabel{{border:2px solid {T.ORANGE};border-radius:3px;}}")

    def dragLeaveEvent(self, e): self.setStyleSheet("")

    def dropEvent(self, e):
        self.setStyleSheet("")
        src = e.mimeData().text()
        if src != self.spell['nom']:
            self._grid.swap_by_name(src, self.spell['nom'])
        e.acceptProposedAction()


# ── SpellGrid ──────────────────────────────────────────────

class SpellGrid(QWidget):
    COLS = 4

    def __init__(self, cls_key, profile_key, parent=None):
        super().__init__(parent)
        self._cls_key = cls_key; self._profile_key = profile_key
        self._spells = list(SPELLS[cls_key])
        self._grey = model.load_config().get(f'challenges_grey_{profile_key}', {})
        # Restaurer ordre
        order = model.load_config().get(f'challenges_order_{profile_key}', [])
        if order:
            by = {s['nom']: s for s in self._spells}
            self._spells = [by[n] for n in order if n in by] + \
                           [s for s in self._spells if s['nom'] not in set(order)]
        self._cards = []; self._gl = None
        self._build()

    def _build(self):
        self._gl = QGridLayout(self)
        self._gl.setSpacing(4); self._gl.setContentsMargins(4, 4, 4, 4)
        for i, spell in enumerate(self._spells):
            card = SpellCard(spell, self._cls_key, self._profile_key, self)
            card.set_greyed(self._grey.get(spell['nom'], False))
            card.toggled_signal.connect(self._on_toggle)
            self._gl.addWidget(card, i // self.COLS, i % self.COLS)
            self._cards.append(card)

    def _on_toggle(self, name, greyed):
        self._grey[name] = greyed
        model.save_config({f'challenges_grey_{self._profile_key}': self._grey})

    def swap_by_name(self, a, b):
        ia = next((i for i,s in enumerate(self._spells) if s['nom']==a), None)
        ib = next((i for i,s in enumerate(self._spells) if s['nom']==b), None)
        if ia is None or ib is None: return
        self._spells[ia], self._spells[ib] = self._spells[ib], self._spells[ia]
        for c in self._cards: self._gl.removeWidget(c); c.deleteLater()
        self._cards = []
        for i, spell in enumerate(self._spells):
            card = SpellCard(spell, self._cls_key, self._profile_key, self)
            card.set_greyed(self._grey.get(spell['nom'], False))
            card.toggled_signal.connect(self._on_toggle)
            self._gl.addWidget(card, i // self.COLS, i % self.COLS)
            self._cards.append(card)
        model.save_config({f'challenges_order_{self._profile_key}':
                           [s['nom'] for s in self._spells]})


# ── ClassPickerPanel (inline) ──────────────────────────────

class ClassPickerPanel(QFrame):
    """Panneau inline de création de personnage."""
    confirmed = Signal(str, str)  # pseudo, cls_key

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};"
                           f"border-radius:4px;}}")
        self._cls_key = 'cra'
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(12, 10, 12, 10); lay.setSpacing(8)

        # Pseudo
        lbl = QLabel("Pseudo")
        lbl.setStyleSheet(f"color:{T.HINT};font-size:8pt;font-weight:bold;border:none;background:transparent;")
        self._pseudo = QLineEdit()
        self._pseudo.setPlaceholderText("Nom du personnage")
        self._pseudo.setStyleSheet(
            f"QLineEdit{{background:{T.SURFACE2};border:1px solid {T.BORDER};"
            f"border-radius:3px;padding:5px 8px;color:{T.TEXT};font-size:9pt;}}"
            f"QLineEdit:focus{{border-color:{T.ORANGE};}}")
        lay.addWidget(lbl); lay.addWidget(self._pseudo)

        # Classe
        lbl2 = QLabel("Classe")
        lbl2.setStyleSheet(f"color:{T.HINT};font-size:8pt;font-weight:bold;border:none;background:transparent;")
        lay.addWidget(lbl2)

        row = QHBoxLayout(); row.setSpacing(6)
        self._cls_btns = {}
        for key, info in CLASS_COLORS.items():
            btn = QPushButton(info['name'])
            btn.setCheckable(True)
            btn.setStyleSheet(
                f"QPushButton{{background:{T.SURFACE};border:2px solid {T.BORDER};"
                f"border-radius:4px;padding:10px 4px;font-weight:bold;color:{T.TEXT};font-size:9pt;}}"
                f"QPushButton:checked{{background:{info['primary']};border-color:{info['primary']};color:white;}}"
                f"QPushButton:hover:!checked{{border-color:{info['primary']};}}")
            btn.clicked.connect(lambda _, k=key: self._select(k))
            row.addWidget(btn); self._cls_btns[key] = btn
        self._cls_btns['cra'].setChecked(True)
        lay.addLayout(row)

        # Confirmer
        confirm = QPushButton("✔  Créer le personnage")
        confirm.setStyleSheet(
            f"QPushButton{{background:{T.ORANGE};color:white;border:none;border-radius:3px;"
            f"padding:8px;font-weight:bold;font-size:9pt;}}"
            f"QPushButton:hover{{background:{T.ORANGE_L};}}")
        confirm.clicked.connect(self._confirm)
        lay.addWidget(confirm)

    def _select(self, key):
        self._cls_key = key
        for k, b in self._cls_btns.items(): b.setChecked(k == key)

    def _confirm(self):
        pseudo = self._pseudo.text().strip() or CLASS_COLORS[self._cls_key]['name']
        cls_key = self._cls_key  # sauvegarder avant reset
        self._pseudo.clear()
        self.confirmed.emit(pseudo, cls_key)  # émettre avec la vraie classe
        self._cls_btns['cra'].setChecked(True); self._cls_key = 'cra'  # reset après


# ── EconomePanel ───────────────────────────────────────────

class EconomePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        saved = model.load_config().get('econome_profiles', [])
        self._profiles = saved if saved else [{'pseudo': 'Personnage 1', 'cls_key': 'cra'}]
        self._current = 0
        self._picker_visible = False
        self._build()

    def _save(self):
        model.save_config({'econome_profiles': [
            {'pseudo': p['pseudo'], 'cls_key': p['cls_key']} for p in self._profiles]})

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(4, 4, 4, 4); lay.setSpacing(6)

        # Boutons + / −
        add_del = QHBoxLayout(); add_del.setSpacing(6)
        self._btn_add = QPushButton("＋  Ajouter un personnage")
        self._btn_add.setStyleSheet(
            f"QPushButton{{background:{T.GREEN};color:white;border:none;border-radius:4px;"
            f"padding:9px 0;font-weight:bold;font-size:9pt;}}"
            f"QPushButton:hover{{background:#6e9428;}}")
        self._btn_add.clicked.connect(self._toggle_picker)

        btn_del = QPushButton("－  Supprimer")
        btn_del.setStyleSheet(
            f"QPushButton{{background:{T.RED};color:white;border:none;border-radius:4px;"
            f"padding:9px 0;font-weight:bold;font-size:9pt;}}"
            f"QPushButton:hover{{background:#9e4840;}}")
        btn_del.clicked.connect(self._del)
        add_del.addWidget(self._btn_add, 1); add_del.addWidget(btn_del, 1)
        lay.addLayout(add_del)

        # Panneau inline création
        self._picker = ClassPickerPanel()
        self._picker.confirmed.connect(self._on_profile_created)
        self._picker.hide()
        lay.addWidget(self._picker)

        # Nav ◀ ▶
        nav = QFrame()
        nav.setStyleSheet(f"QFrame{{background:{T.BG_DARK};border:1px solid {T.BORDER};border-radius:4px;}}")
        nl = QHBoxLayout(nav); nl.setContentsMargins(6, 4, 6, 4); nl.setSpacing(4)
        self._prev = QPushButton("◀"); self._prev.setFixedWidth(32)
        self._prev.setStyleSheet(f"QPushButton{{background:transparent;border:none;"
            f"color:{T.HINT};font-size:11pt;font-weight:bold;}}"
            f"QPushButton:hover{{color:{T.ORANGE};}}")
        self._prev.clicked.connect(self._go_prev)
        self._nav_lbl = QLabel("")
        self._nav_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._nav_lbl.setStyleSheet(f"font-weight:bold;font-size:9pt;color:{T.TEXT};")
        self._nav_lbl.mouseDoubleClickEvent = lambda e: self._rename()
        self._next = QPushButton("▶"); self._next.setFixedWidth(32)
        self._next.setStyleSheet(f"QPushButton{{background:transparent;border:none;"
            f"color:{T.HINT};font-size:11pt;font-weight:bold;}}"
            f"QPushButton:hover{{color:{T.ORANGE};}}")
        self._next.clicked.connect(self._go_next)
        nl.addWidget(self._prev); nl.addWidget(self._nav_lbl, 1); nl.addWidget(self._next)
        lay.addWidget(nav)

        self._grid_container = QWidget()
        self._grid_container.setStyleSheet("background:transparent;")
        self._grid_lay = QVBoxLayout(self._grid_container)
        self._grid_lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._grid_container)

        self._refresh_grid(); self._update_nav()

    def _toggle_picker(self):
        self._picker_visible = not self._picker_visible
        self._picker.setVisible(self._picker_visible)
        # Quand caché, le widget ne doit plus prendre de place
        from PySide6.QtWidgets import QSizePolicy
        sp = self._picker.sizePolicy()
        if self._picker_visible:
            sp.setVerticalPolicy(QSizePolicy.Policy.Preferred)
        else:
            sp.setVerticalPolicy(QSizePolicy.Policy.Fixed)
        self._picker.setSizePolicy(sp)
        self._picker.setMaximumHeight(16777215 if self._picker_visible else 0)
        self._btn_add.setText("✕  Fermer" if self._picker_visible else "＋  Ajouter un personnage")
        self._btn_add.setStyleSheet(
            f"QPushButton{{background:{'#8c4038' if self._picker_visible else T.GREEN};"
            f"color:white;border:none;border-radius:4px;padding:9px 0;font-weight:bold;font-size:9pt;}}"
            f"QPushButton:hover{{background:{'#9e4840' if self._picker_visible else '#6e9428'};}}")
        self._fit()

    def _on_profile_created(self, pseudo, cls_key):
        if len(self._profiles) < 8:
            self._profiles.append({'pseudo': pseudo, 'cls_key': cls_key})
            self._save(); self._current = len(self._profiles) - 1
            self._refresh_grid(); self._update_nav()
        self._toggle_picker()

    def _refresh_grid(self):
        while self._grid_lay.count():
            item = self._grid_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if self._current < len(self._profiles):
            p = self._profiles[self._current]
            # Clé stable basée sur le pseudo, pas l'index
            key = f"{p.get('pseudo', str(self._current))}_{p['cls_key']}"
            g = SpellGrid(p['cls_key'], key)
            self._grid_lay.addWidget(g)
            self._grid_lay.addStretch()
        self._fit()

    def _fit(self):
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        def do():
            # Remonter la chaîne updateGeometry() pour propager le changement
            w = self
            while w:
                w.updateGeometry()
                w = w.parentWidget()
            root = self.window()
            if not root: return
            root.setMinimumHeight(0)
            root.setMaximumHeight(16777215)
            root.adjustSize()
        QTimer.singleShot(0, do)

    def _update_nav(self):
        if not self._profiles: return
        p = self._profiles[self._current]
        info = CLASS_COLORS[p['cls_key']]
        n = len(self._profiles)
        self._nav_lbl.setText(f"{p['pseudo']}  ·  {info['name']}  ({self._current+1}/{n})")
        self._nav_lbl.setStyleSheet(f"font-weight:bold;font-size:9pt;color:{info['primary']};")
        self._prev.setEnabled(self._current > 0)
        self._next.setEnabled(self._current < n - 1)

    def _go_prev(self):
        if self._current > 0: self._current -= 1; self._refresh_grid(); self._update_nav()

    def _go_next(self):
        if self._current < len(self._profiles)-1: self._current += 1; self._refresh_grid(); self._update_nav()

    def _del(self):
        if len(self._profiles) <= 1: return
        del self._profiles[self._current]
        self._current = min(self._current, len(self._profiles)-1)
        self._save(); self._refresh_grid(); self._update_nav()

    def _rename(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Renommer", "Pseudo :",
                                        text=self._profiles[self._current]['pseudo'])
        if ok and name.strip():
            self._profiles[self._current]['pseudo'] = name.strip()
            self._save(); self._update_nav()


# ── PartagePanel ───────────────────────────────────────────

class PartagePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries = []
        self._build(); self._load()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(12, 10, 12, 10); lay.setSpacing(6)

        info = QLabel("Renseigne les pseudos et active le toggle quand le personnage a tué.")
        info.setStyleSheet(f"color:{T.HINT};font-size:9pt;font-style:italic;")
        info.setWordWrap(True); lay.addWidget(info)

        hdr = QHBoxLayout(); hdr.setContentsMargins(22, 0, 0, 0)
        lp = QLabel("Personnage"); lp.setStyleSheet(f"color:{T.SUBTEXT};font-weight:bold;font-size:9pt;")
        lt = QLabel("A tué"); lt.setStyleSheet(f"color:{T.SUBTEXT};font-weight:bold;font-size:9pt;")
        hdr.addWidget(lp); hdr.addStretch(); hdr.addWidget(lt)
        lay.addLayout(hdr); lay.addWidget(_sep())

        for i in range(8):
            row = QHBoxLayout(); row.setSpacing(8)
            num = QLabel(f"{i+1}.")
            num.setStyleSheet(f"color:{T.HINT};font-weight:bold;font-size:9pt;"); num.setFixedWidth(20)
            entry = QLineEdit(); entry.setPlaceholderText(f"Pseudo {i+1}")
            entry.setStyleSheet(
                f"QLineEdit{{border:1px solid {T.BORDER};border-radius:3px;padding:5px 8px;"
                f"background:{T.SURFACE2};color:{T.TEXT};font-size:9pt;}}"
                f"QLineEdit:focus{{border-color:{T.ORANGE};}}")
            entry.textChanged.connect(self._save)
            toggle = QPushButton(); toggle.setCheckable(True); toggle.setFixedSize(44, 24)
            toggle.setStyleSheet(
                f"QPushButton{{background:{T.BG_DARK};border-radius:12px;border:none;}}"
                f"QPushButton:checked{{background:{T.GREEN};}}")
            toggle.toggled.connect(self._save)
            row.addWidget(num); row.addWidget(entry, 1); row.addWidget(toggle)
            lay.addLayout(row); self._entries.append((entry, toggle))

        lay.addWidget(_sep())
        reset = QPushButton("↺  Tout remettre à zéro")
        reset.setStyleSheet(
            f"QPushButton{{background:transparent;border:1px solid {T.RED};color:{T.RED};"
            f"border-radius:3px;padding:6px;font-weight:bold;}}"
            f"QPushButton:hover{{background:rgba(140,64,56,0.08);}}")
        reset.clicked.connect(self._reset); lay.addWidget(reset); lay.addStretch()

    def _save(self):
        model.save_config({'challenges_partage':
            [{'pseudo': e.text(), 'killed': b.isChecked()} for e, b in self._entries]})

    def _load(self):
        data = model.load_config().get('challenges_partage', [])
        for i, item in enumerate(data[:8]):
            self._entries[i][0].setText(item.get('pseudo', ''))
            self._entries[i][1].setChecked(item.get('killed', False))

    def _reset(self):
        for _, b in self._entries: b.setChecked(False)
        self._save()


# ── ChallengesTab ──────────────────────────────────────────

class ChallengesTab(QWidget):
    def sizeHint(self):
        # Calculer la hauteur réelle des widgets visibles
        lay = self.layout()
        if not lay: return super().sizeHint()
        h = 0
        for i in range(lay.count()):
            item = lay.itemAt(i)
            if item and item.widget() and item.widget().isVisible():
                h += item.widget().sizeHint().height() + lay.spacing()
        m = lay.contentsMargins()
        return __import__('PySide6.QtCore', fromlist=['QSize']).QSize(
            self.width(), h + m.top() + m.bottom())

    def __init__(self, parent=None):
        super().__init__(parent); self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(8, 8, 8, 8); lay.setSpacing(6)
        row = QHBoxLayout(); row.setSpacing(6)
        self._btn_eco = QPushButton("💰  Économe"); self._btn_eco.setCheckable(True)
        self._btn_part = QPushButton("👥  Partage"); self._btn_part.setCheckable(True)
        for btn in (self._btn_eco, self._btn_part):
            btn.setStyleSheet(
                f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};border:none;"
                f"border-radius:3px;padding:8px 16px;font-weight:bold;font-size:9pt;}}"
                f"QPushButton:checked{{background:{T.ORANGE};color:white;}}")
        self._btn_eco.clicked.connect(lambda: self._set_mode('econome'))
        self._btn_part.clicked.connect(lambda: self._set_mode('partage'))
        row.addWidget(self._btn_eco); row.addWidget(self._btn_part); row.addStretch()
        lay.addLayout(row); lay.addWidget(_sep())
        self._stack = QStackedWidget()
        self._econome = EconomePanel(); self._partage = PartagePanel()
        self._stack.addWidget(self._econome); self._stack.addWidget(self._partage)
        lay.addWidget(self._stack)
        saved = model.load_config().get('challenges_mode', 'econome')
        self._set_mode(saved, save=False)

    def _set_mode(self, mode, save=True):
        self._stack.setCurrentIndex(0 if mode == 'econome' else 1)
        self._btn_eco.setChecked(mode == 'econome')
        self._btn_part.setChecked(mode == 'partage')
        if save: model.save_config({'challenges_mode': mode})
