"""tabs/dashboard_tab.py — Dashboard personnages par compte."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy, QDialog, QLineEdit,
    QFormLayout, QDialogButtonBox, QComboBox
)
from PySide6.QtCore import Qt, QSize
import model, theme

T = theme
CFG_KEY = "dashboard"

# ── Données ────────────────────────────────────────────────
# Structure :
# {"accounts": [
#   {"name": "Compte Principal", "chars": [
#     {"pseudo": "St-Arc", "classe": "Cra", "niveau": 200, "serveur": "Algathe",
#      "kamas": 12450000, "pods": "2450/6000",
#      "equip": {"coiffe":"...","cape":"...",...},
#      "notes": "..."}
#   ]}
# ]}

SLOTS = [
    ("coiffe",   "Coiffe",   "👒"),
    ("cape",     "Cape",     "🧣"),
    ("anneau1",  "Anneau G", "💍"),
    ("anneau2",  "Anneau D", "💍"),
    ("amulette", "Amulette", "📿"),
    ("ceinture", "Ceinture", "👜"),
    ("bottes",   "Bottes",   "👟"),
    ("familier", "Familier", "🐾"),
    ("drago",    "Drago",    "🐉"),
    ("dofus1",   "Dofus 1",  "🥚"),
    ("dofus2",   "Dofus 2",  "🥚"),
    ("dofus3",   "Dofus 3",  "🥚"),
    ("dofus4",   "Dofus 4",  "🥚"),
    ("dofus5",   "Dofus 5",  "🥚"),
    ("dofus6",   "Dofus 6",  "🥚"),
]

CLASSES = [
    "Cra",      "Enutrof",  "Pandawa",
    "Sacrieur", "Iop",      "Féca",
    "Ecaflip",  "Eniripsa", "Xélor",
    "Sram",     "Sadida",   "Osamodas",
]

CLASS_COLORS = {
    "Cra": "#4e9458", "Enutrof": "#b8962a", "Pandawa": "#7b4e96",
    "Sacrieur": "#8c4038", "Iop": "#4e6e96", "Féca": "#4e8a96",
    "Ecaflip": "#4e8a7a", "Eniripsa": "#c4952a", "Xélor": "#6a6a9a",
    "Sram": "#5a5a5a", "Sadida": "#5e8020", "Osamodas": "#7a5a20",
}

# Mapping classe → nom de fichier image (dans pictures/classes/)
CLASS_IMG = {
    "Cra":      "cra.png",
    "Enutrof":  "enutrof.png",
    "Pandawa":  "pandawa.png",
    "Sacrieur": "sacrieur.png",
    "Iop":      "iop.png",
    "Féca":     "feca.png",
    "Ecaflip":  "ecaflip.png",
    "Eniripsa": "eniripsa.png",
    "Xélor":    "xelor.png",
    "Sram":     "sram.png",
    "Sadida":   "sadida.png",
    "Osamodas": "osamodas.png",
      # alias
}

def _get_class_img_path(classe: str):
    """Retourne le chemin absolu de l'image de classe, ou None si absent."""
    import sys
    from pathlib import Path
    filename = CLASS_IMG.get(classe)
    if not filename:
        return None
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent.parent
    path = base / "pictures" / "classes" / filename
    return str(path) if path.exists() else None


def _load_data():
    return model.load_config().get(CFG_KEY, {"accounts": []})

def _save_data(data):
    model.save_config({CFG_KEY: data})

def _sep():
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"color:{T.BORDER};max-height:1px;background:{T.BORDER};border:none;")
    f.setFixedHeight(1)
    return f

def _lbl(text, color=None, size="9pt", bold=False, italic=False, wrap=False):
    l = QLabel(text)
    ss = f"background:transparent;font-size:{size};"
    if color:  ss += f"color:{color};"
    if bold:   ss += "font-weight:bold;"
    if italic: ss += "font-style:italic;"
    l.setStyleSheet(ss)
    if wrap: l.setWordWrap(True)
    return l

def _bss(bg, fg, hbg, brd=None):
    b = f"border:none;" if brd else "border:none;"
    return (f"QPushButton{{background:{bg};color:{fg};{b}"
            f"padding:4px 8px;font-size:8pt;font-weight:bold;}}"
            f"QPushButton:hover{{background:{hbg};}}")


# ── SlotWidget ─────────────────────────────────────────────

class SlotWidget(QFrame):
    """Un emplacement d'équipement cliquable."""

    def __init__(self, key, label, icon, value, on_edit, parent=None):
        super().__init__(parent)
        self._key = key
        self._on_edit = on_edit
        self._empty = not value
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(54)
        self._build(label, icon, value)
        self._update_style()

    def _build(self, label, icon, value):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 5, 6, 5)
        lay.setSpacing(3)

        # Icône + label sur une ligne
        top = QHBoxLayout(); top.setSpacing(5); top.setContentsMargins(0,0,0,0)
        ico = QLabel(icon)
        ico.setFixedSize(22, 22)
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico.setStyleSheet(
            "background:transparent;font-size:15pt;border:none;padding:0;"
            "font-family:'Segoe UI Emoji';")
        lbl = QLabel(label)
        lbl.setStyleSheet(
            "background:transparent;border:none;"
            f"color:{T.HINT};font-size:8pt;font-family:'Segoe UI';font-weight:normal;")
        top.addWidget(ico); top.addWidget(lbl); top.addStretch()
        lay.addLayout(top)

        self._val_lbl = QLabel(value if value else "")
        self._val_lbl.setStyleSheet(
            "background:transparent;border:none;"
            f"font-family:'Segoe UI';font-size:9.5pt;"
            + (f"color:{T.TEXT};font-weight:bold;" if value else f"color:{T.HINT};"))
        self._val_lbl.setWordWrap(False)
        lay.addWidget(self._val_lbl)

    def _update_style(self):
        if not self._empty:
            self.setStyleSheet(
                f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER2};}}"
                f"QFrame:hover{{border:1px solid {T.ORANGE};}}")
        else:
            self.setStyleSheet(
                f"QFrame{{background:{T.BG_DARK};border:1px solid {T.BORDER};}}"
                f"QFrame:hover{{border:1px solid {T.ORANGE};background:{T.SURFACE2};}}")

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._on_edit(self._key)

    def set_value(self, value):
        self._empty = not value
        self._val_lbl.setText(value if value else "")
        self._val_lbl.setStyleSheet(
            "background:transparent;border:none;"
            f"font-family:'Segoe UI';font-size:9.5pt;"
            + (f"color:{T.TEXT};font-weight:bold;" if value else f"color:{T.HINT};"))
        self._update_style()


# ── CharWidget ─────────────────────────────────────────────

class CharWidget(QFrame):
    """Widget d'un personnage — ligne cliquable + panneau dépliable."""

    def __init__(self, char_data, account_idx, char_idx, on_refresh, parent=None):
        super().__init__(parent)
        self._char = char_data
        self._acc_idx = account_idx
        self._char_idx = char_idx
        self._on_refresh = on_refresh
        self._expanded = False
        self._slot_widgets: dict = {}
        self.setObjectName("char_frame")
        self.setStyleSheet("QFrame#char_frame{background:transparent;border:none;}")
        self._build()

    def _build(self):
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0,0,0,0)
        self._lay.setSpacing(0)

        # ── Ligne résumé ────────────────────────────────────
        self._header = QFrame()
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setStyleSheet(
            "QFrame{background:transparent;border:none;}"
            f"QFrame:hover{{background:{T.SURFACE2};}}")
        h_lay = QHBoxLayout(self._header)
        h_lay.setContentsMargins(10,6,10,6); h_lay.setSpacing(8)

        # Avatar — image classe si disponible, sinon couleur + initiale
        cls = self._char.get("classe","?")
        color = CLASS_COLORS.get(cls, T.HINT)
        avatar = QLabel()
        avatar.setFixedSize(26,26)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_path = _get_class_img_path(cls)
        if img_path:
            from PySide6.QtGui import QPixmap
            pix = QPixmap(img_path).scaled(
                24, 24,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            avatar.setPixmap(pix)
            avatar.setStyleSheet(
                f"background:{color};"
                f"border:none;padding:1px;")
        else:
            avatar.setText(cls[:2] if cls else "?")
            avatar.setStyleSheet(
                f"background:{color};color:white;"
                f"font-size:8px;font-weight:bold;border:none;")
        h_lay.addWidget(avatar)

        # Nom + compte/classe
        info = QWidget(); info.setStyleSheet("background:transparent;")
        il = QVBoxLayout(info); il.setContentsMargins(0,0,0,0); il.setSpacing(1)
        il.addWidget(_lbl(self._char.get("pseudo","?"), T.TEXT, "11pt", bold=True))
        sub = f"{cls} · Niv. {self._char.get('niveau','?')}"
        if self._char.get("serveur"): sub += f" · {self._char['serveur']}"
        il.addWidget(_lbl(sub, T.HINT, "8.5pt"))
        h_lay.addWidget(info, 1)

        # Kamas + Pods
        km = self._char.get("kamas", 0)
        km_str = f"{km/1_000_000:.1f}M" if km >= 1_000_000 else (
                  f"{km//1000}K" if km >= 1000 else str(km))
        stats = QWidget(); stats.setStyleSheet("background:transparent;")
        sl = QHBoxLayout(stats); sl.setContentsMargins(0,0,0,0); sl.setSpacing(10)
        q1 = QWidget(); q1.setStyleSheet("background:transparent;")
        ql1 = QVBoxLayout(q1); ql1.setContentsMargins(0,0,0,0); ql1.setSpacing(0)
        ql1.addWidget(_lbl(km_str, T.GOLD, "9.5pt", bold=True))
        ql1.addWidget(_lbl("Kamas", T.HINT, "7pt"))
        sl.addWidget(q1)
        h_lay.addWidget(stats)

        # Flèche
        self._arrow = QLabel("▶")
        self._arrow.setStyleSheet(f"color:{T.HINT};font-size:8pt;background:transparent;")
        h_lay.addWidget(self._arrow)

        self._header.mousePressEvent = lambda e: self._toggle()
        self._lay.addWidget(self._header)

        # ── Panel dépliable ─────────────────────────────────
        self._panel = QWidget()
        self._panel.setStyleSheet(
            f"background:{T.SURFACE2};border:none;")
        pl = QVBoxLayout(self._panel)
        pl.setContentsMargins(10,8,10,8); pl.setSpacing(6)

        # Stats
        sg = QFrame(); sg.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border:none;}}")
        sg_lay = QHBoxLayout(sg); sg_lay.setContentsMargins(8,6,8,6); sg_lay.setSpacing(0)
        for val, lbl_txt, color in [
            (km_str,                            "Kamas",  T.GOLD),
            (str(self._char.get("niveau","?")), "Niveau", T.GREEN),
            (self._char.get("serveur","—"),     "Serveur",T.TEXT),
        ]:
            col = QWidget(); col.setStyleSheet("background:transparent;")
            cl = QVBoxLayout(col); cl.setContentsMargins(0,0,0,0); cl.setSpacing(1)
            cl.addWidget(_lbl(val, color, "11pt", bold=True))
            cl.addWidget(_lbl(lbl_txt, T.HINT, "8pt"))
            sg_lay.addWidget(col, 1)
        pl.addWidget(sg)

        # Hint équipement
        hint = _lbl("✏️  Clique sur un emplacement pour noter l'objet équipé",
                    T.HINT, "8pt", italic=True)
        hint.setWordWrap(True)
        pl.addWidget(hint)

        # Équipement
        eq_frame = QFrame()
        eq_frame.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border:none;}}")
        eq_lay = QVBoxLayout(eq_frame)
        eq_lay.setContentsMargins(8,7,8,7); eq_lay.setSpacing(4)
        eq_lay.addWidget(_lbl("🛡 Équipement", T.HINT, "8.5pt", bold=True))

        equip = self._char.get("equip", {})
        def add_row(keys):
            row = QHBoxLayout(); row.setSpacing(8)
            for key, label, icon in [s for s in SLOTS if s[0] in keys]:
                sw = SlotWidget(key, label, icon,
                                equip.get(key,""),
                                self._edit_slot)
                self._slot_widgets[key] = sw
                row.addWidget(sw)
            eq_lay.addLayout(row)

        add_row(["coiffe",   "cape"])
        add_row(["anneau1",  "anneau2"])
        add_row(["amulette"])
        add_row(["ceinture", "bottes"])
        add_row(["familier", "drago"])

        # Dofus section — titre simple
        dof_sep = _lbl("🥚 Dofus", T.HINT, "8.5pt", bold=True)
        eq_lay.addWidget(dof_sep)

        dof1 = QHBoxLayout(); dof1.setSpacing(8)
        for key in ["dofus1","dofus2","dofus3"]:
            _, label, icon = next(s for s in SLOTS if s[0]==key)
            sw = SlotWidget(key, label, icon, equip.get(key,""), self._edit_slot)
            self._slot_widgets[key] = sw
            dof1.addWidget(sw)
        eq_lay.addLayout(dof1)

        dof2 = QHBoxLayout(); dof2.setSpacing(8)
        for key in ["dofus4","dofus5","dofus6"]:
            _, label, icon = next(s for s in SLOTS if s[0]==key)
            sw = SlotWidget(key, label, icon, equip.get(key,""), self._edit_slot)
            self._slot_widgets[key] = sw
            dof2.addWidget(sw)
        eq_lay.addLayout(dof2)
        pl.addWidget(eq_frame)

        # Notes
        notes_frame = QFrame()
        notes_frame.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border:none;}}")
        nf_lay = QVBoxLayout(notes_frame)
        nf_lay.setContentsMargins(8,6,8,6); nf_lay.setSpacing(3)
        nf_lay.addWidget(_lbl("📝 Notes", T.HINT, "8.5pt", bold=True))
        self._notes_lbl = _lbl(
            self._char.get("notes","") or "Aucune note.",
            T.SUBTEXT, "9pt", italic=True, wrap=True)
        nf_lay.addWidget(self._notes_lbl)
        pl.addWidget(notes_frame)

        # Boutons
        act = QHBoxLayout(); act.setSpacing(5)
        btn_edit = QPushButton("✎ Modifier")
        btn_edit.setStyleSheet(_bss(T.SURFACE, T.SUBTEXT, T.BG_DARK, T.BORDER))
        btn_edit.clicked.connect(self._edit_char)
        btn_del = QPushButton("🗑 Supprimer")
        btn_del.setStyleSheet(_bss(T.SURFACE, T.RED, "#f5e8e8", T.BORDER))
        btn_del.clicked.connect(self._delete_char)
        act.addWidget(btn_edit); act.addWidget(btn_del)
        pl.addLayout(act)

        self._panel.hide()
        self._lay.addWidget(self._panel)

    def _toggle(self):
        self._expanded = not self._expanded
        self._panel.setVisible(self._expanded)
        self._arrow.setText("▼" if self._expanded else "▶")
        self._arrow.setStyleSheet(
            f"color:{T.ORANGE if self._expanded else T.HINT};"
            f"font-size:8pt;background:transparent;")
        self._header.setStyleSheet(
            f"QFrame{{background:{T.SURFACE2 if self._expanded else 'transparent'};"
            f"border:none;}}"
            f"QFrame:hover{{background:{T.SURFACE2};}}")

    def _edit_slot(self, key):
        _, label, icon = next(s for s in SLOTS if s[0] == key)
        cur = self._char.get("equip", {}).get(key, "")
        text, ok = _input_dialog(self, f"{icon} {label}", "Nom de l'item :", cur)
        if ok:
            all_data = _load_data()
            all_data["accounts"][self._acc_idx]["chars"][self._char_idx].setdefault("equip", {})[key] = text
            _save_data(all_data)
            self._char.setdefault("equip", {})[key] = text
            self._slot_widgets[key].set_value(text)

    def _edit_char(self):
        dlg = CharDialog(self._char.copy(), self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            char_data = dlg.get_data()
            all_data = _load_data()
            all_data["accounts"][self._acc_idx]["chars"][self._char_idx].update(char_data)
            _save_data(all_data)
            self._on_refresh()

    def _delete_char(self):
        data = _load_data()
        data["accounts"][self._acc_idx]["chars"].pop(self._char_idx)
        _save_data(data)
        self._on_refresh()


# ── AccountWidget ──────────────────────────────────────────

class AccountWidget(QFrame):
    """Carte d'un compte avec ses personnages."""

    def __init__(self, account_data, acc_idx, on_refresh, parent=None):
        super().__init__(parent)
        self._acc = account_data
        self._acc_idx = acc_idx
        self._on_refresh = on_refresh
        self.setObjectName("card")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        # Header compte
        hdr = QFrame()
        hdr.setStyleSheet(
            f"QFrame{{background:{T.BG_DARK};border-bottom:1px solid {T.BORDER};}}")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(10,5,8,5); hl.setSpacing(6)

        hl.addWidget(_lbl("👤", size="10pt"))
        hl.addWidget(_lbl(self._acc.get("name","Compte"), T.TEXT, "9pt", bold=True), 1)

        n = len(self._acc.get("chars",[]))
        badge = QLabel(f"{n} perso{'s' if n>1 else ''}")
        badge.setStyleSheet(
            f"background:{T.ORANGE};color:white;font-size:6.5pt;font-weight:bold;"
            f"padding:2px 5px;")
        hl.addWidget(badge)

        # Label hint qui apparaît au hover
        self._hint_lbl = QLabel("")
        self._hint_lbl.setStyleSheet(
            f"color:{T.ORANGE};font-size:7pt;background:transparent;")
        hl.addWidget(self._hint_lbl)

        btn_rename = QPushButton("✎")
        btn_rename.setFixedSize(22, 22)
        btn_rename.setStyleSheet(
            f"QPushButton{{background:transparent;color:{T.TEXT};border:none;font-size:11pt;padding:0;}}"
            f"QPushButton:hover{{color:{T.ORANGE};}}")
        btn_rename.entered = lambda: self._hint_lbl.setText("Renommer")
        btn_rename.leaved  = lambda: self._hint_lbl.setText("")
        btn_rename.installEventFilter(self)
        btn_rename.clicked.connect(self._rename_account)
        btn_rename.setObjectName("rename_btn")
        hl.addWidget(btn_rename)

        btn_del_acc = QPushButton("✕")
        btn_del_acc.setFixedSize(22, 22)
        btn_del_acc.setStyleSheet(
            f"QPushButton{{background:transparent;color:{T.TEXT};border:none;font-size:11pt;padding:0;}}"
            f"QPushButton:hover{{color:{T.RED};}}")
        btn_del_acc.entered = lambda: self._hint_lbl.setText("Supprimer")
        btn_del_acc.entered_color = T.RED
        btn_del_acc.leaved  = lambda: self._hint_lbl.setText("")
        btn_del_acc.installEventFilter(self)
        btn_del_acc.setObjectName("delete_btn")
        btn_del_acc.clicked.connect(self._delete_account)
        hl.addWidget(btn_del_acc)
        lay.addWidget(hdr)

        # Panel de confirmation suppression (caché par défaut)
        self._confirm_panel = QFrame()
        self._confirm_panel.setStyleSheet(
            f"QFrame{{background:{T.SURFACE2};border-bottom:1px solid {T.BORDER};}}")
        cp_lay = QHBoxLayout(self._confirm_panel)
        cp_lay.setContentsMargins(10, 6, 10, 6); cp_lay.setSpacing(8)
        name = self._acc.get("name","?")
        cp_lay.addWidget(_lbl(f"Supprimer « {name} » ?", T.TEXT, "8.5pt"))
        cp_lay.addStretch()
        btn_yes = QPushButton("✔ Oui")
        btn_yes.setStyleSheet(
            f"QPushButton{{background:{T.RED};color:white;border:none;"
            f"padding:4px 10px;font-size:8pt;font-weight:bold;}}"
            f"QPushButton:hover{{background:#9e4840;}}")
        btn_no = QPushButton("Annuler")
        btn_no.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};border:none;"
            f"padding:4px 10px;font-size:8pt;font-weight:bold;}}"
            f"QPushButton:hover{{color:{T.TEXT};}}")
        btn_yes.clicked.connect(self._confirm_delete)
        btn_no.clicked.connect(lambda: self._confirm_panel.hide())
        cp_lay.addWidget(btn_yes); cp_lay.addWidget(btn_no)
        self._confirm_panel.hide()
        lay.addWidget(self._confirm_panel)

        # Personnages
        for i, char in enumerate(self._acc.get("chars",[])):
            cw = CharWidget(char, self._acc_idx, i, self._on_refresh)
            lay.addWidget(cw)

        # Bouton ajouter perso
        btn_add = QPushButton("＋  Ajouter un personnage")
        btn_add.setStyleSheet(
            f"QPushButton{{background:transparent;color:{T.HINT};border:none;"
            f"border-top:1px solid {T.BORDER};padding:6px 10px;"
            f"text-align:left;font-size:7.5pt;}}"
            f"QPushButton:hover{{color:{T.ORANGE};background:{T.SURFACE2};}}")
        btn_add.clicked.connect(self._add_char)
        lay.addWidget(btn_add)

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.Type.Enter and hasattr(obj, 'entered'):
            obj.entered()
            if hasattr(obj, 'entered_color'):
                self._hint_lbl.setStyleSheet(
                    f"color:{obj.entered_color};font-size:7pt;background:transparent;")
            else:
                self._hint_lbl.setStyleSheet(
                    f"color:{T.ORANGE};font-size:7pt;background:transparent;")
        elif event.type() == QEvent.Type.Leave and hasattr(obj, 'leaved'):
            obj.leaved()
        return super().eventFilter(obj, event)

    def _rename_account(self):
        text, ok = _input_dialog(self, "Renommer le compte", "Nom du compte :",
                                 self._acc.get("name",""))
        if ok and text:
            all_data = _load_data()
            all_data["accounts"][self._acc_idx]["name"] = text
            _save_data(all_data)
            self._on_refresh()

    def _delete_account(self):
        # Afficher le panel de confirmation inline (toggle)
        visible = self._confirm_panel.isVisible()
        self._confirm_panel.setVisible(not visible)

    def _confirm_delete(self):
        data = _load_data()
        data["accounts"].pop(self._acc_idx)
        _save_data(data)
        self._on_refresh()

    def _add_char(self):
        dlg = CharDialog({}, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            char_data = dlg.get_data()
            # Recharger, modifier, sauvegarder
            all_data = _load_data()
            all_data["accounts"][self._acc_idx].setdefault("chars", []).append(char_data)
            _save_data(all_data)
            self._on_refresh()


# ── Dialogs ────────────────────────────────────────────────

def _input_dialog(parent, title, label, default=""):
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setFixedWidth(300)
    dlg.setStyleSheet(f"QDialog{{background:{T.BG};}}")
    lay = QVBoxLayout(dlg); lay.setSpacing(8); lay.setContentsMargins(14,12,14,12)
    lay.addWidget(_lbl(label, T.SUBTEXT, "8pt"))
    inp = QLineEdit(default or "")
    inp.setStyleSheet(
        f"QLineEdit{{background:{T.SURFACE};border:none;"
        f"padding:5px 8px;color:{T.TEXT};font-size:9pt;}}"
        f"QLineEdit:focus{{border-color:{T.ORANGE};}}")
    lay.addWidget(inp)
    btns = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    btns.accepted.connect(dlg.accept)
    btns.rejected.connect(dlg.reject)
    lay.addWidget(btns)
    inp.setFocus(); inp.selectAll()
    ok = dlg.exec() == QDialog.DialogCode.Accepted
    return inp.text().strip(), ok


class ClassPickerDialog(QDialog):
    """Grille de sélection de classe avec images."""

    def __init__(self, current, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choisir une classe")
        self.setStyleSheet(f"QDialog{{background:{T.BG};}}")
        self.setFixedWidth(300)
        self._selected = current
        self._build()

    def _build(self):
        from PySide6.QtGui import QPixmap
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10,10,10,10); lay.setSpacing(8)
        lay.addWidget(_lbl("Sélectionne une classe", T.SUBTEXT, "8pt", bold=True))

        grid_w = QWidget(); grid_w.setStyleSheet("background:transparent;")
        from PySide6.QtWidgets import QGridLayout
        grid = QGridLayout(grid_w)
        grid.setContentsMargins(0,0,0,0); grid.setSpacing(6)

        row, col = 0, 0
        for cls in CLASSES:
            btn = QPushButton()
            btn.setFixedSize(48, 48)
            btn.setToolTip(cls)
            img_path = _get_class_img_path(cls)
            color = CLASS_COLORS.get(cls, T.HINT)
            if img_path:
                from PySide6.QtGui import QPixmap, QIcon
                pix = QPixmap(img_path).scaled(
                    36, 36,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
                btn.setIcon(QIcon(pix))
                btn.setIconSize(QSize(36,36))
                btn.setText("")
            else:
                btn.setText(cls[:3])
                btn.setStyleSheet(
                    f"QPushButton{{background:{color};color:white;"
                    f"font-size:7pt;font-weight:bold;border:none;}}")
            border = f"3px solid {T.ORANGE}" if cls == self._selected else f"1px solid {T.BORDER}"
            btn.setStyleSheet(btn.styleSheet() +
                f"QPushButton{{background:{color};border:{border};padding:2px;}}"
                f"QPushButton:hover{{border:none;}}")
            btn.clicked.connect(lambda _, c=cls, b=btn: self._select(c))
            grid.addWidget(btn, row, col)
            col += 1
            if col >= 4: col = 0; row += 1

        lay.addWidget(grid_w)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)
        self.adjustSize()

    def _select(self, cls):
        self._selected = cls
        self.accept()

    def get_class(self):
        return self._selected


class CharDialog(QDialog):
    """Dialogue de création / édition d'un personnage."""

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data
        self.setWindowTitle("Personnage")
        self.setFixedWidth(320)
        self.setStyleSheet(f"QDialog{{background:{T.BG};}}")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14,12,14,12); lay.setSpacing(6)
        lay.addWidget(_lbl("Informations du personnage", T.SUBTEXT, "8pt", bold=True))

        def field(label, key, placeholder=""):
            row = QWidget(); row.setStyleSheet("background:transparent;")
            rl = QVBoxLayout(row); rl.setContentsMargins(0,0,0,0); rl.setSpacing(2)
            rl.addWidget(_lbl(label, T.HINT, "7.5pt"))
            inp = QLineEdit(str(self._data.get(key,"") or ""))
            inp.setPlaceholderText(placeholder)
            inp.setStyleSheet(
                f"QLineEdit{{background:{T.SURFACE};border:none;"
                f"padding:4px 7px;color:{T.TEXT};font-size:8.5pt;}}"
                f"QLineEdit:focus{{border-color:{T.ORANGE};}}")
            rl.addWidget(inp)
            lay.addWidget(row)
            return inp

        self._pseudo  = field("Pseudo",  "pseudo",  "St-Arc-[A13]")
        self._niveau  = field("Niveau",  "niveau",  "200")
        # Serveur — liste fixe
        srv_row = QWidget(); srv_row.setStyleSheet("background:transparent;")
        sl2 = QVBoxLayout(srv_row); sl2.setContentsMargins(0,0,0,0); sl2.setSpacing(2)
        sl2.addWidget(_lbl("Serveur", T.HINT, "7.5pt"))
        self._serveur = QComboBox()
        self._serveur.addItems(["Boune", "Allisteria", "Fallanster"])
        cur_srv = self._data.get("serveur", "Boune")
        if cur_srv in ["Boune", "Allisteria", "Fallanster"]:
            self._serveur.setCurrentText(cur_srv)
        self._serveur.setStyleSheet(
            f"QComboBox{{background:{T.SURFACE};border:none;"
            f"padding:4px 7px;color:{T.TEXT};font-size:8.5pt;}}"
            f"QComboBox QAbstractItemView{{background:{T.SURFACE};"
            f"selection-background-color:{T.ORANGE};color:{T.TEXT};}}")
        sl2.addWidget(self._serveur)
        lay.addWidget(srv_row)
        self._kamas = field("Kamas", "kamas", "0")

        # Classe — bouton qui ouvre le picker d'images
        cls_row = QWidget(); cls_row.setStyleSheet("background:transparent;")
        cl = QVBoxLayout(cls_row); cl.setContentsMargins(0,0,0,0); cl.setSpacing(2)
        cl.addWidget(_lbl("Classe", T.HINT, "7.5pt"))
        self._selected_cls = self._data.get("classe","Cra")
        cls_pick_row = QHBoxLayout(); cls_pick_row.setSpacing(6)
        self._cls_avatar = QLabel()
        self._cls_avatar.setFixedSize(32,32)
        self._cls_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cls_btn = QPushButton(self._selected_cls)
        self._cls_btn.setStyleSheet(
            f"QPushButton{{background:{T.SURFACE};color:{T.TEXT};"
            f"border:none;"
            f"padding:4px 10px;font-size:8.5pt;text-align:left;}}"
            f"QPushButton:hover{{border-color:{T.ORANGE};}}")
        self._cls_btn.clicked.connect(self._pick_class)
        cls_pick_row.addWidget(self._cls_avatar)
        cls_pick_row.addWidget(self._cls_btn, 1)
        cl.addLayout(cls_pick_row)
        lay.addWidget(cls_row)
        self._update_cls_preview()

        # Notes
        notes_row = QWidget(); notes_row.setStyleSheet("background:transparent;")
        nl = QVBoxLayout(notes_row); nl.setContentsMargins(0,0,0,0); nl.setSpacing(2)
        nl.addWidget(_lbl("Notes", T.HINT, "7.5pt"))
        self._notes = QLineEdit(self._data.get("notes","") or "")
        self._notes.setPlaceholderText("Objectif, stuff cible…")
        self._notes.setStyleSheet(
            f"QLineEdit{{background:{T.SURFACE};border:none;"
            f"padding:4px 7px;color:{T.TEXT};font-size:8.5pt;}}"
            f"QLineEdit:focus{{border-color:{T.ORANGE};}}")
        nl.addWidget(self._notes)
        lay.addWidget(notes_row)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _pick_class(self):
        dlg = ClassPickerDialog(self._selected_cls, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._selected_cls = dlg.get_class()
            self._cls_btn.setText(self._selected_cls)
            self._update_cls_preview()

    def _update_cls_preview(self):
        from PySide6.QtGui import QPixmap
        cls = self._selected_cls
        color = CLASS_COLORS.get(cls, T.HINT)
        img_path = _get_class_img_path(cls)
        if img_path:
            pix = QPixmap(img_path).scaled(
                28, 28,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            self._cls_avatar.setPixmap(pix)
            self._cls_avatar.setStyleSheet(
                f"background:{color};"
                f"border:none;padding:1px;")
        else:
            self._cls_avatar.setText(cls[:2])
            self._cls_avatar.setStyleSheet(
                f"background:{color};color:white;"
                f"font-size:8px;font-weight:bold;border:none;")

    def get_data(self):
        try: kamas = int(self._kamas.text().replace(" ","").replace(",","") or 0)
        except ValueError: kamas = 0
        return {
            "pseudo":  self._pseudo.text().strip(),
            "classe":  self._selected_cls,
            "niveau":  self._niveau.text().strip(),
            "serveur": self._serveur.currentText(),
            "kamas":   kamas,
            "notes":   self._notes.text().strip(),
            "equip":   self._data.get("equip", {}),
        }


# ── Helpers data ───────────────────────────────────────────

def _save_dashboard():
    """Sauvegarde les données depuis la dernière version chargée."""
    pass  # géré directement dans les widgets via _load_data/_save_data


# ── DashboardTab ───────────────────────────────────────────

class DashboardTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        # ── Scroll area fixe 500px max ─────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFixedHeight(480)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{background:{T.BG};border:none;}}
            QScrollBar:vertical {{background:{T.BG_DARK};width:5px;}}
            QScrollBar::handle:vertical {{background:{T.BORDER2};min-height:20px;}}
            QScrollBar::handle:vertical:hover {{background:{T.ORANGE};}}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{height:0;}}
        """)

        self._inner = QWidget()
        self._inner.setStyleSheet(f"background:{T.BG};")
        self._inner_lay = QVBoxLayout(self._inner)
        self._inner_lay.setContentsMargins(8,8,8,8); self._inner_lay.setSpacing(8)

        self._scroll.setWidget(self._inner)
        lay.addWidget(self._scroll)

        # ── Footer : bouton ajouter compte ────────────────
        footer = QWidget()
        footer.setStyleSheet(
            f"background:{T.BG_DARK};border-top:1px solid {T.BORDER};")
        footer.setFixedHeight(36)
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(8,0,8,0)
        btn_add_acc = QPushButton("＋  Ajouter un compte")
        btn_add_acc.setStyleSheet(
            f"QPushButton{{background:transparent;color:{T.ORANGE};"
            f"border:none;font-size:8.5pt;font-weight:bold;}}"
            f"QPushButton:hover{{color:{T.ORANGE_L};}}")
        btn_add_acc.clicked.connect(self._add_account)
        fl.addWidget(btn_add_acc)
        fl.addStretch()
        lay.addWidget(footer)

        self._refresh()

    def _refresh(self):
        # Vider la liste
        while self._inner_lay.count():
            item = self._inner_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        data = _load_data()
        accounts = data.get("accounts", [])

        if not accounts:
            empty = _lbl(
                "Aucun compte.\nClique sur ＋ Ajouter un compte pour commencer.",
                T.HINT, "9pt", italic=True, wrap=True)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setContentsMargins(20,40,20,40)
            self._inner_lay.addWidget(empty)
        else:
            for i, acc in enumerate(accounts):
                aw = AccountWidget(acc, i, self._refresh)
                self._inner_lay.addWidget(aw)

        self._inner_lay.addStretch()

    def _add_account(self):
        text, ok = _input_dialog(self, "Nouveau compte", "Nom du compte :", "")
        if ok and text:
            data = _load_data()
            data.setdefault("accounts",[]).append({"name": text, "chars": []})
            _save_data(data)
            self._refresh()

    def sizeHint(self):
        return QSize(350, 516)  # scroll(480) + footer(36)
