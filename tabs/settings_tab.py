"""tabs/settings_tab.py — Paramètres : thèmes intégrés + thèmes personnalisés."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QInputDialog, QMessageBox,
    QColorDialog, QSizePolicy, QDialog, QLineEdit, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import model, theme

T = theme


def _section(title):
    l = QLabel(title)
    l.setStyleSheet(
        f"background:transparent;color:{T.HINT};font-size:8pt;font-weight:700;")
    return l


def _card():
    f = QFrame()
    f.setStyleSheet(
        f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};"
        f"border-radius:10px;}}"
        f"QLabel{{background:transparent;border:none;}}")
    return f


def _lbl(text, color=None, size="9pt", bold=False):
    l = QLabel(text)
    c = color or T.TEXT
    w = "700" if bold else "400"
    l.setStyleSheet(
        f"font-size:{size};color:{c};font-weight:{w};background:transparent;")
    return l


# ── Dialogs custom (thème correct) ───────────────────────────────────

def _input_dialog(parent, title: str, label: str) -> tuple[str, bool]:
    """QInputDialog remplacé par dialog custom au bon thème."""
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setFixedWidth(280)
    dlg.setStyleSheet(
        f"QDialog{{background:{T.BG};color:{T.TEXT};}}"
        f"QLabel{{background:transparent;color:{T.TEXT};font-size:9pt;}}"
        f"QLineEdit{{background:{T.SURFACE};color:{T.TEXT};"
        f"border:1px solid {T.BORDER};border-radius:6px;padding:5px 8px;font-size:9pt;}}"
        f"QLineEdit:focus{{border-color:{T.ORANGE};}}"
        f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};"
        f"border:1px solid {T.BORDER};border-radius:6px;"
        f"padding:5px 14px;font-size:9pt;font-weight:600;}}"
        f"QPushButton:hover{{background:{T.BORDER};color:{T.TEXT};}}")

    from PySide6.QtWidgets import QLineEdit
    lay = QVBoxLayout(dlg); lay.setContentsMargins(16,14,16,14); lay.setSpacing(10)
    lay.addWidget(QLabel(label))
    edit = QLineEdit(); edit.setFixedHeight(32)
    lay.addWidget(edit)

    btn_row = QHBoxLayout(); btn_row.setSpacing(8)
    btn_row.addStretch()
    btn_ok = QPushButton("OK")
    btn_ok.setFixedHeight(30)
    btn_ok.setStyleSheet(
        f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});"
        f"color:white;border:none;border-radius:6px;font-size:9pt;font-weight:700;}}")
    btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_cancel = QPushButton("Annuler")
    btn_cancel.setFixedHeight(30)
    btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_ok.clicked.connect(dlg.accept)
    btn_cancel.clicked.connect(dlg.reject)
    btn_row.addWidget(btn_cancel); btn_row.addWidget(btn_ok)
    lay.addLayout(btn_row)

    ok = dlg.exec() == QDialog.DialogCode.Accepted
    return edit.text(), ok


def _warn_dialog(parent, title: str, message: str):
    """QMessageBox remplacé par dialog custom au bon thème."""
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setFixedWidth(280)
    dlg.setStyleSheet(
        f"QDialog{{background:{T.BG};color:{T.TEXT};}}"
        f"QLabel{{background:transparent;color:{T.TEXT};font-size:9pt;}}"
        f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};"
        f"border:1px solid {T.BORDER};border-radius:6px;"
        f"padding:5px 18px;font-size:9pt;font-weight:600;}}"
        f"QPushButton:hover{{background:{T.BORDER};color:{T.TEXT};}}")

    lay = QVBoxLayout(dlg); lay.setContentsMargins(16,14,16,14); lay.setSpacing(12)
    msg = QLabel(message); msg.setWordWrap(True)
    lay.addWidget(msg)
    btn_row = QHBoxLayout(); btn_row.addStretch()
    btn_ok = QPushButton("OK")
    btn_ok.setFixedHeight(30)
    btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_ok.clicked.connect(dlg.accept)
    btn_row.addWidget(btn_ok)
    lay.addLayout(btn_row)
    dlg.exec()


# ── Éditeur thème (QDialog) ────────────────────────────────────────────

class ThemeEditorDialog(QDialog):
    """Fenêtre modale d'édition de thème, largeur = app."""

    FIELDS = [
        ("Fonds", [
            ("BG",      "Fond principal"),
            ("BG_DARK", "Surface / cartes"),
            ("SURFACE", "Fond éléments"),
        ]),
        ("Texte", [
            ("TEXT",    "Texte principal"),
            ("SUBTEXT", "Texte secondaire"),
            ("HINT",    "Texte discret"),
        ]),
        ("Accents", [
            ("GRAD1", "Couleur principale"),
            ("GRAD2", "Couleur secondaire"),
            ("RED",   "Rouge / erreur"),
        ]),
    ]

    def __init__(self, name: str, palette: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Thème : {name}")
        self.setFixedWidth(700)
        self.setModal(True)
        self._name    = name
        self._palette = dict(palette)
        self._saved   = False
        self._pickers = {}
        self._build()
        self._restyle()

    def _restyle(self):
        p = T
        # IMPORTANT : tous les sélecteurs ciblent #pickerZone (le widget qui contient
        # les color pickers), JAMAIS le mockup (#themeMockup) qui garde ses styles
        # inline intacts, sans aucune interférence du QSS global de la dialog.
        self.setStyleSheet(
            f"QDialog{{background:{p.BG};color:{p.TEXT};}}"
            f"#pickerZone QLabel{{background:transparent;color:{p.TEXT};}}"
            f"#pickerZone QPushButton{{background:{p.BG_DARK};color:{p.SUBTEXT};"
            f"border:1px solid {p.BORDER};border-radius:6px;"
            f"padding:4px 10px;font-size:9pt;font-weight:600;}}"
            f"#pickerZone QPushButton:hover{{background:{p.BORDER};color:{p.TEXT};}}"
            f"QLabel#dlgTitle{{background:transparent;color:{p.TEXT};}}"
            f"QFrame#sep{{background:{p.BORDER};max-height:1px;border:none;}}"
            f"QFrame#grp{{background:{p.SURFACE};border:1px solid {p.BORDER};"
            f"border-radius:8px;}}"
            f"QPushButton#btnSave{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {p.GRAD1},stop:1 {p.GRAD2});color:white;border:none;"
            f"border-radius:6px;font-size:9pt;font-weight:700;}}"
            f"QPushButton#btnCancel{{background:{p.BG_DARK};color:{p.SUBTEXT};"
            f"border:1px solid {p.BORDER};border-radius:6px;"
            f"padding:5px 14px;font-size:9pt;font-weight:600;}}"
            f"QPushButton#btnCancel:hover{{background:{p.BORDER};color:{p.TEXT};}}")

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14); root.setSpacing(10)

        # Titre
        title = QLabel(f"✏  {self._name}")
        title.setStyleSheet(
            f"font-size:10pt;font-weight:700;color:{T.TEXT};background:transparent;")
        root.addWidget(title)

        # ── Corps : pickers à gauche, maquette à droite ──
        body = QHBoxLayout()
        body.setSpacing(16)

        # Colonne gauche : color pickers
        left = QVBoxLayout()
        left.setSpacing(10)

        for group_name, fields in self.FIELDS:
            grp_lbl = QLabel(group_name.upper())
            grp_lbl.setStyleSheet(
                f"font-size:7pt;font-weight:700;letter-spacing:1px;"
                f"color:{T.HINT};background:transparent;")
            left.addWidget(grp_lbl)

            grp = QFrame(); grp.setObjectName("grp")
            gl  = QVBoxLayout(grp)
            gl.setContentsMargins(10, 8, 10, 8); gl.setSpacing(6)

            for key, label in fields:
                val    = self._palette.get(key, "#ffffff")
                row    = QHBoxLayout(); row.setSpacing(8); row.setContentsMargins(0,0,0,0)

                dot = QPushButton()
                dot.setFixedSize(26, 26)
                dot.setCursor(Qt.CursorShape.PointingHandCursor)
                dot.setStyleSheet(
                    f"QPushButton{{background:{val};border:2px solid {T.BORDER2};"
                    f"border-radius:6px;}}"
                    f"QPushButton:hover{{border-color:{T.ORANGE};}}")
                dot.clicked.connect(lambda _, k=key, b=dot: self._pick(k, b))

                hex_lbl = QLabel(val)
                hex_lbl.setFixedWidth(56)
                hex_lbl.setStyleSheet(
                    f"font-size:8pt;color:{T.HINT};background:transparent;")

                name_lbl = QLabel(label)
                name_lbl.setStyleSheet(
                    f"font-size:9pt;color:{T.TEXT};background:transparent;")
                name_lbl.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

                row.addWidget(dot)
                row.addWidget(hex_lbl)
                row.addWidget(name_lbl)
                gl.addLayout(row)

                self._pickers[key] = (dot, hex_lbl)

            left.addWidget(grp)

        left.addStretch()

        left_w = QWidget()
        left_w.setObjectName("pickerZone")
        left_w.setLayout(left)
        left_w.setFixedWidth(290)
        body.addWidget(left_w)

        # Colonne droite : maquette aperçu live, prend tout l'espace restant
        right = QVBoxLayout()
        right.setSpacing(8)
        right_lbl = QLabel("APERÇU EN DIRECT")
        right_lbl.setStyleSheet(
            f"font-size:7pt;font-weight:700;letter-spacing:1px;"
            f"color:{T.HINT};background:transparent;")
        right.addWidget(right_lbl)

        self._build_mockup()
        right.addWidget(self._mock)
        right.addStretch()

        right_w = QWidget()
        right_w.setLayout(right)
        body.addWidget(right_w, 1)

        root.addLayout(body)

        # Séparateur
        sep = QFrame(); sep.setObjectName("sep")
        sep.setFrameShape(QFrame.Shape.HLine); sep.setMaximumHeight(1)
        root.addWidget(sep)

        # Boutons bas
        btn_row = QHBoxLayout(); btn_row.setSpacing(8)

        btn_save = QPushButton("💾  Enregistrer")
        btn_save.setFixedHeight(32)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});"
            f"color:white;border:none;border-radius:6px;"
            f"font-size:9pt;font-weight:700;}}"
            f"QPushButton:hover{{opacity:0.9;}}")
        btn_save.clicked.connect(self._save)

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setFixedHeight(32)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)

        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        root.addLayout(btn_row)

    def _build_mockup(self) -> QFrame:
        """Vraie maquette de l'onglet Comptes, RECONSTRUITE avec les VRAIS
        types de widgets du code source (QPushButton pour Discord/⛶/onglets,
        pas QLabel) pour que les border-radius s'affichent identiquement à
        l'app réelle. Hauteurs et espacements copiés exactement."""
        from tabs.accounts.characters_panel import (
            _SVG_STAR_ON, _SVG_STAR_OFF, _SVG_CROSS, _SVG_EXCLUDE,
        )
        self._mock_svg_star_on  = _SVG_STAR_ON
        self._mock_svg_star_off = _SVG_STAR_OFF
        self._mock_svg_cross    = _SVG_CROSS
        self._mock_svg_exclude  = _SVG_EXCLUDE

        frame = QFrame()
        frame.setObjectName("themeMockup")
        self._mock = frame
        frame.setFixedWidth(350)
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)

        # ── Titlebar (hauteur réelle 46px, icône 28px, Discord = QPushButton) ──
        self._mock_tb = QFrame()
        self._mock_tb.setFixedHeight(46)
        tb_lay = QHBoxLayout(self._mock_tb)
        tb_lay.setContentsMargins(12, 0, 10, 0); tb_lay.setSpacing(8)

        self._mock_tb_icon = QLabel("🎮")
        self._mock_tb_icon.setFixedSize(28, 28)
        self._mock_tb_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tb_lay.addWidget(self._mock_tb_icon)

        self._mock_tb_title = QLabel("Retro Toolbox")
        self._mock_tb_title.setStyleSheet(
            "font-size:12pt;font-weight:700;background:transparent;color:white;")
        tb_lay.addWidget(self._mock_tb_title)
        tb_lay.addStretch()

        # Discord : VRAI QPushButton, setFixedHeight(28), radius:14 (pilule)
        self._mock_tb_badge = QPushButton("💬 Discord")
        self._mock_tb_badge.setFixedHeight(28)
        tb_lay.addWidget(self._mock_tb_badge)

        # ⛶ : VRAI QPushButton, setFixedSize(28,28), radius:7
        self._mock_tb_sq = QPushButton("⛶")
        self._mock_tb_sq.setFixedSize(28, 28)
        tb_lay.addWidget(self._mock_tb_sq)
        outer.addWidget(self._mock_tb)

        # ── Barre d'onglets : VRAIS QPushButton, 100px fixe, radius:8 ──
        self._mock_tbar = QFrame()
        tbl = QHBoxLayout(self._mock_tbar)
        tbl.setContentsMargins(4, 4, 4, 4); tbl.setSpacing(3)
        self._mock_tabs = []
        for i, txt in enumerate(["👥 Personnages", "⌨ Raccourcis", "⚙ Paramètres"]):
            t = QPushButton(txt)
            t.setFixedHeight(26)
            t.setFixedWidth(100)
            tbl.addWidget(t)
            self._mock_tabs.append((t, i == 0))
        tbl.addStretch()
        self._mock_tab_help = QPushButton("Tuto")
        self._mock_tab_help.setFixedHeight(26)
        tbl.addWidget(self._mock_tab_help)
        outer.addWidget(self._mock_tbar)

        # ── Barre Modes : VRAIS QPushButton pilules, radius:14 ──
        self._mock_mbar = QFrame()
        mb_lay = QVBoxLayout(self._mock_mbar)
        mb_lay.setContentsMargins(8, 4, 8, 4); mb_lay.setSpacing(3)
        self._mock_mode_lbl = QLabel("Mode :")
        self._mock_mode_lbl.setStyleSheet("font-size:9pt;font-weight:700;background:transparent;")
        mb_lay.addWidget(self._mock_mode_lbl)
        pills_row1 = QHBoxLayout(); pills_row1.setSpacing(8)
        pills_row2 = QHBoxLayout(); pills_row2.setSpacing(8)
        self._mock_pills = []
        for txt in ("🌾 Farm OFF", "👟 Déplacement OFF"):
            pill = QPushButton(txt)
            pill.setFixedHeight(26)
            pills_row1.addWidget(pill)
            self._mock_pills.append(pill)
        pills_row1.addStretch()
        for txt in ("🌿 Farm Sadi OFF",):
            pill = QPushButton(txt)
            pill.setFixedHeight(26)
            pills_row2.addWidget(pill)
            self._mock_pills.append(pill)
        pills_row2.addStretch()
        mb_lay.addLayout(pills_row1)
        mb_lay.addLayout(pills_row2)
        outer.addWidget(self._mock_mbar)

        # ── Header "Fenêtres Dofus" + compteur ───────────────
        self._mock_hdr = QFrame()
        self._mock_hdr.setFixedHeight(36)
        hdr_lay = QHBoxLayout(self._mock_hdr)
        hdr_lay.setContentsMargins(10, 0, 10, 0); hdr_lay.setSpacing(6)
        self._mock_hdr_title = QLabel("Fenêtres Dofus")
        self._mock_hdr_title.setStyleSheet("font-size:9pt;font-weight:700;background:transparent;")
        hdr_lay.addWidget(self._mock_hdr_title, 1)
        self._mock_hdr_count = QLabel("1 fenêtre")
        self._mock_hdr_count.setStyleSheet("font-size:8pt;background:transparent;")
        hdr_lay.addWidget(self._mock_hdr_count)
        outer.addWidget(self._mock_hdr)

        # ── 1 ligne de compte — boutons SVG identiques au mode compact ──
        self._mock_rows_frame = QFrame()
        rows_lay = QVBoxLayout(self._mock_rows_frame)
        rows_lay.setContentsMargins(0, 0, 0, 0); rows_lay.setSpacing(0)

        row = QFrame()
        row.setMinimumHeight(64)
        r_outer = QVBoxLayout(row)
        r_outer.setContentsMargins(10, 9, 10, 9); r_outer.setSpacing(7)

        r1 = QHBoxLayout(); r1.setSpacing(6)
        hdl = QLabel("⠿")
        hdl.setFixedWidth(12)
        r1.addWidget(hdl)
        rang = QLabel("1.")
        rang.setFixedWidth(16)
        r1.addWidget(rang)
        name = QLabel("St-Arc-[A13]")
        name.setStyleSheet("font-size:10pt;font-weight:700;background:transparent;")
        r1.addWidget(name, 1)
        r_outer.addLayout(r1)

        r2 = QHBoxLayout(); r2.setSpacing(6)
        r2.addStretch()
        star_btn = QPushButton()
        star_btn.setFixedSize(28, 28)
        r2.addWidget(star_btn)
        excl_btn = QPushButton()
        excl_btn.setFixedSize(28, 28)
        r2.addWidget(excl_btn)
        r_outer.addLayout(r2)

        rows_lay.addWidget(row)
        self._mock_rows = [(row, hdl, rang, name, star_btn, excl_btn)]
        outer.addWidget(self._mock_rows_frame)

        # ── Footer hint ────────────────────────────────────
        self._mock_ftr = QFrame()
        self._mock_ftr.setFixedHeight(28)
        ftr_lay = QVBoxLayout(self._mock_ftr)
        ftr_lay.setContentsMargins(10, 0, 10, 0); ftr_lay.setSpacing(0)
        self._mock_ftr_lbl = QLabel("⠿ Glisse pour réordonner  ·  ★ = principal  ·  ○ = exclure")
        self._mock_ftr_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self._mock_ftr_lbl.setStyleSheet("font-size:8pt;font-style:italic;background:transparent;")
        ftr_lay.addWidget(self._mock_ftr_lbl)
        outer.addWidget(self._mock_ftr)

        # ── Bouton "Appliquer l'ordre" : VRAI QPushButton, radius:8 ──
        self._mock_btn_order = QPushButton("🖥  Appliquer l'ordre dans la barre des tâches")
        self._mock_btn_order.setFixedHeight(34)
        outer.addWidget(self._mock_btn_order)

        # ── Profils d'ordre ───────────────────────────────────
        self._mock_prof = QFrame()
        pl = QVBoxLayout(self._mock_prof)
        pl.setContentsMargins(8, 8, 8, 8); pl.setSpacing(6)

        self._mock_prof_title = QLabel("📋 Profils d'ordre")
        self._mock_prof_title.setStyleSheet("font-size:10pt;font-weight:700;background:transparent;")
        pl.addWidget(self._mock_prof_title)

        self._mock_prof_combo = QComboBox()
        self._mock_prof_combo.setFixedHeight(30)
        self._mock_prof_combo.addItem("pl sadi")
        pl.addWidget(self._mock_prof_combo)

        row_ap = QHBoxLayout(); row_ap.setSpacing(5)
        self._mock_prof_apply = QPushButton("▶  Appliquer")
        self._mock_prof_apply.setFixedHeight(30)
        row_ap.addWidget(self._mock_prof_apply)
        self._mock_prof_del = QPushButton("✕  Supprimer")
        self._mock_prof_del.setFixedHeight(30)
        row_ap.addWidget(self._mock_prof_del)
        pl.addLayout(row_ap)

        self._mock_prof_save = QPushButton("💾  Nommer et sauvegarder cet ordre")
        self._mock_prof_save.setFixedHeight(32)
        pl.addWidget(self._mock_prof_save)

        outer.addWidget(self._mock_prof)

        # ── Navbar du bas : VRAIS QPushButton, 56px, icône+label 2 lignes ──
        self._mock_navbar = QFrame()
        nav_lay = QHBoxLayout(self._mock_navbar)
        nav_lay.setContentsMargins(0, 0, 0, 0); nav_lay.setSpacing(0)
        self._mock_nav_items = []
        for i, (icon, label) in enumerate([
            ("👥", "Comptes"), ("👤", "Dashboard"), ("💰", "Prix HDV"),
            ("📝", "Notes"), ("⋯", "Plus"),
        ]):
            btn = QPushButton(f"{icon}\n{label}")
            btn.setFixedHeight(56)
            nav_lay.addWidget(btn, 1)
            self._mock_nav_items.append((btn, i == 0))
        outer.addWidget(self._mock_navbar)

        self._refresh_mockup()
        return frame

    def _refresh_mockup(self):
        from PySide6.QtGui import QPixmap, QIcon
        from PySide6.QtCore import QByteArray

        def _svg_pixmap(svg: str, size=18) -> QPixmap:
            px = QPixmap()
            px.loadFromData(QByteArray(svg.encode()), "SVG")
            return px.scaled(size, size,
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)

        p = self._full_palette()

        self._mock.setStyleSheet(
            f"QFrame{{background:{p['BG']};border:1px solid {p['BORDER']};}}")

        # Titlebar
        self._mock_tb.setStyleSheet(
            f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {p['GRAD1']},stop:1 {p['GRAD2']});border:none;}}")
        self._mock_tb_icon.setStyleSheet(
            "font-size:14pt;background:rgba(255,255,255,30);border-radius:7px;")
        self._mock_tb_title.setStyleSheet(
            "font-size:12pt;font-weight:700;background:transparent;color:white;")

        # Discord : copie EXACTE du QSS réel (radius:14px = pilule complète sur 28px)
        self._mock_tb_badge.setStyleSheet(
            "QPushButton{background:rgba(255,255,255,51);color:white;"
            "border:1px solid rgba(255,255,255,89);border-radius:14px;"
            "padding:3px 12px;font-size:9pt;font-weight:700;}"
            "QPushButton:hover{background:rgba(255,255,255,76);}")

        # ⛶ : copie EXACTE du QSS réel (radius:7px sur 28x28)
        self._mock_tb_sq.setStyleSheet(
            "QPushButton{background:rgba(255,255,255,51);color:white;"
            "border:1px solid rgba(255,255,255,89);border-radius:7px;"
            "font-size:11pt;font-weight:700;padding:0;}"
            "QPushButton:hover{background:rgba(255,255,255,76);}")

        # Barre onglets
        self._mock_tbar.setStyleSheet(
            f"QFrame{{background:{p['SURFACE']};border:none;"
            f"border-bottom:1px solid {p['BORDER']};}}")
        for t, active in self._mock_tabs:
            if active:
                t.setStyleSheet(
                    f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                    f"stop:0 {p['GRAD1']},stop:1 {p['GRAD2']});color:white;"
                    f"border:2px solid transparent;border-radius:8px;"
                    f"font-size:8pt;font-weight:700;padding:3px 6px;}}")
            else:
                t.setStyleSheet(
                    f"QPushButton{{background:{p['SURFACE']};color:{p['HINT']};"
                    f"border:2px solid transparent;border-radius:8px;"
                    f"font-size:8pt;font-weight:700;padding:3px 6px;}}")
        self._mock_tab_help.setStyleSheet(
            f"QPushButton{{background:{p['SURFACE']};color:{p['GRAD1']};"
            f"border:none;font-size:8pt;font-weight:bold;padding:2px 8px;}}")

        # mbar
        self._mock_mbar.setStyleSheet(
            f"QFrame{{background:{p['BG_DARK']};border:none;"
            f"border-bottom:1px solid {p['BORDER']};}}")
        self._mock_mode_lbl.setStyleSheet(
            f"font-size:9pt;font-weight:700;background:transparent;color:{p['HINT']};")
        for pill in self._mock_pills:
            pill.setStyleSheet(
                f"QPushButton{{background:{p['BG_DARK']};color:{p['HINT']};"
                f"border:1px solid {p['BORDER']};border-radius:14px;"
                f"padding:3px 12px;font-size:9pt;font-weight:700;}}")

        # Header
        self._mock_hdr.setStyleSheet(f"QFrame{{background:{p['BG_DARK']};border:none;}}")
        self._mock_hdr_title.setStyleSheet(
            f"font-size:9pt;font-weight:700;background:transparent;color:{p['TEXT']};")
        self._mock_hdr_count.setStyleSheet(
            f"font-size:8pt;background:transparent;color:{p['HINT']};")

        # Liste comptes
        self._mock_rows_frame.setStyleSheet(f"QFrame{{background:{p['BG']};border:none;}}")
        for row, hdl, rang, name, star_btn, excl_btn in self._mock_rows:
            row.setStyleSheet(
                f"QFrame{{background:{p['SURFACE']};border:none;"
                f"border-bottom:1px solid {p['BORDER']};}}")
            hdl.setStyleSheet(f"font-size:11pt;background:transparent;color:{p['HINT']};")
            rang.setStyleSheet(f"font-size:8pt;background:transparent;color:{p['HINT']};")
            name.setStyleSheet(
                f"font-size:10pt;font-weight:700;background:transparent;color:{p['TEXT']};")

            # SVG identiques au mode compact : pas de bordure, radius:6, fond selon état
            star_btn.setStyleSheet(
                f"QPushButton{{background:rgba(217,121,31,45);border:none;"
                f"border-radius:6px;padding:0;}}"
                f"QPushButton:hover{{background:rgba(255,255,255,30);}}")
            star_px = _svg_pixmap(self._mock_svg_star_on)
            star_btn.setIcon(QIcon(star_px))
            star_btn.setIconSize(star_px.size())

            excl_btn.setStyleSheet(
                f"QPushButton{{background:{p['BG_DARK']};border:none;"
                f"border-radius:6px;padding:0;}}"
                f"QPushButton:hover{{background:rgba(255,255,255,30);}}")
            excl_px = _svg_pixmap(self._mock_svg_exclude)
            excl_btn.setIcon(QIcon(excl_px))
            excl_btn.setIconSize(excl_px.size())

        # Footer
        self._mock_ftr.setStyleSheet(f"QFrame{{background:{p['SURFACE']};border:none;}}")
        self._mock_ftr_lbl.setStyleSheet(
            f"font-size:8pt;font-style:italic;background:transparent;color:{p['HINT']};")

        # Bouton ordre
        self._mock_btn_order.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {p['GRAD1']},stop:1 {p['GRAD2']});color:white;border:none;"
            f"padding:4px 10px;font-size:10pt;font-weight:700;border-radius:8px;}}")

        # Profils d'ordre — fond BG_DARK comme le vrai prof_frame
        self._mock_prof.setStyleSheet(f"QFrame{{background:{p['BG_DARK']};border:none;}}")
        self._mock_prof_title.setStyleSheet(
            f"font-size:10pt;font-weight:700;background:transparent;color:{p['TEXT']};")
        self._mock_prof_combo.setStyleSheet(
            f"QComboBox{{background:{p['SURFACE']};color:{p['TEXT']};border:none;"
            f"padding:4px 8px;font-size:9pt;}}"
            f"QComboBox QAbstractItemView{{background:{p['SURFACE']};color:{p['TEXT']};"
            f"selection-background-color:{p['GRAD1']};}}")
        self._mock_prof_apply.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {p['GRAD1']},stop:1 {p['GRAD2']});color:white;border:none;"
            f"padding:4px 10px;font-size:9pt;font-weight:700;border-radius:8px;}}")
        self._mock_prof_del.setStyleSheet(
            f"QPushButton{{background:{p['BG_DARK']};color:{p['RED']};"
            f"border:1px solid {p['BORDER']};"
            f"padding:4px 10px;font-size:9pt;font-weight:700;border-radius:8px;}}")
        self._mock_prof_save.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {p['GRAD1']},stop:1 {p['GRAD2']});color:white;border:none;"
            f"padding:4px 10px;font-size:10pt;font-weight:700;border-radius:8px;}}")

        # Navbar — copie EXACTE du QSS de NavButton réel
        for btn, active in self._mock_nav_items:
            if active:
                btn.setStyleSheet(
                    f"QPushButton{{background:{p['SURFACE']};color:{p['GRAD1']};"
                    f"border:none;border-top:2px solid {p['GRAD1']};"
                    f"font-size:9pt;font-weight:bold;padding:4px 2px;}}")
            else:
                btn.setStyleSheet(
                    f"QPushButton{{background:{p['BG_DARK']};color:{p['HINT']};"
                    f"border:none;font-size:9pt;font-weight:bold;padding:4px 2px;}}")

    def _pick(self, key: str, btn: QPushButton):
        current = self._palette.get(key, "#ffffff")
        c = QColorDialog.getColor(QColor(current), self, "Choisir une couleur")
        if not c.isValid():
            return
        hex_val = c.name()
        self._palette[key] = hex_val
        dot, hex_lbl = self._pickers[key]
        dot.setStyleSheet(
            f"QPushButton{{background:{hex_val};border:2px solid {T.BORDER2};"
            f"border-radius:6px;}}"
            f"QPushButton:hover{{border-color:{T.ORANGE};}}")
        hex_lbl.setText(hex_val)
        # Dériver ORANGE/GREEN depuis GRAD1
        if key == "GRAD1":
            self._palette["ORANGE"] = hex_val
            self._palette["GREEN"]  = hex_val
            try:
                r,g,b = int(hex_val[1:3],16), int(hex_val[3:5],16), int(hex_val[5:7],16)
                r2 = min(255, r+30); g2 = min(255, g+30); b2 = min(255, b+30)
                self._palette["ORANGE_L"] = f"#{r2:02x}{g2:02x}{b2:02x}"
            except Exception:
                pass
        if key == "GRAD2":
            self._palette["ORANGE_D"] = hex_val
        self._refresh_mockup()

    def _full_palette(self) -> dict:
        base = dict(theme.BUILTIN_THEMES["sombre"])
        base.update(self._palette)
        # Dériver les clés manquantes
        base.setdefault("SURFACE2", base["BG"])
        base.setdefault("BORDER",   base["BG_DARK"])
        base.setdefault("BORDER2",  base["HINT"])
        return base

    def _save(self):
        self._saved  = True
        self._result_palette = self._full_palette()
        self.accept()

    @property
    def result_palette(self):
        return getattr(self, "_result_palette", self._full_palette())

    @property
    def saved(self):
        return self._saved


# ── Onglet Paramètres ──────────────────────────────────────────────────

class SettingsTab(QWidget):
    def __init__(self, data_file_path, on_change_folder, parent=None):
        super().__init__(parent)
        self._on_change = on_change_folder
        self._build(data_file_path)

    def _build(self, path):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")

        inner  = QWidget()
        lay    = QVBoxLayout(inner)
        lay.setContentsMargins(12, 14, 12, 14); lay.setSpacing(12)

        # ── Dossier ──────────────────────────────────────
        lay.addWidget(_section("📁  DOSSIER DES DONNÉES"))
        card1 = _card()
        c1 = QVBoxLayout(card1); c1.setContentsMargins(14,12,14,12); c1.setSpacing(8)
        self._path_lbl = QLabel(path)
        self._path_lbl.setStyleSheet(
            f"font-size:8pt;color:{T.SUBTEXT};background:{T.SURFACE2};"
            f"padding:6px 10px;border-radius:6px;")
        self._path_lbl.setWordWrap(True)
        c1.addWidget(self._path_lbl)
        btn_folder = QPushButton("📂  Changer de dossier")
        btn_folder.setFixedHeight(32)
        btn_folder.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});"
            f"color:white;border:none;border-radius:8px;"
            f"font-size:9pt;font-weight:700;}}"
            f"QPushButton:hover{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});}}")
        btn_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_folder.clicked.connect(self._on_change)
        c1.addWidget(btn_folder)
        lay.addWidget(card1)

        # ── Notifications / Ne pas déranger ──────────────
        lay.addWidget(_section("🔕  NOTIFICATIONS"))
        card_dnd = _card()
        cd = QVBoxLayout(card_dnd); cd.setContentsMargins(14,12,14,12); cd.setSpacing(8)

        self._dnd_status_lbl = QLabel("Vérification…")
        self._dnd_status_lbl.setWordWrap(True)
        self._dnd_status_lbl.setStyleSheet(
            f"font-size:8pt;color:{T.SUBTEXT};background:{T.SURFACE2};"
            f"padding:6px 10px;border-radius:6px;")
        cd.addWidget(self._dnd_status_lbl)
        lay.addWidget(card_dnd)
        self._refresh_dnd_status()

        # ── Thèmes intégrés (2×2) ────────────────────────
        lay.addWidget(_section("🎨  THÈMES"))
        card2 = _card()
        c2 = QVBoxLayout(card2); c2.setContentsMargins(14,12,14,12); c2.setSpacing(8)

        lbl_bi = _lbl("Thèmes intégrés", T.HINT, "8pt")
        c2.addWidget(lbl_bi)

        self._theme_btns = {}
        grid = QGridLayout(); grid.setSpacing(6); grid.setContentsMargins(0,0,0,0)
        items = list(theme.BUILTIN_LABELS.items())
        for i, (key, label) in enumerate(items):
            btn = QPushButton(label)
            btn.setFixedHeight(30)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, k=key: self._apply_builtin(k))
            self._theme_btns[key] = btn
            grid.addWidget(btn, i // 2, i % 2)
        c2.addLayout(grid)

        # Séparateur
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine); sep.setMaximumHeight(1)
        sep.setStyleSheet(f"background:{T.BORDER};border:none;")
        c2.addWidget(sep)

        # Thèmes personnalisés
        lbl_cu = _lbl("Thèmes personnalisés", T.HINT, "8pt")
        c2.addWidget(lbl_cu)

        self._custom_list = QVBoxLayout()
        self._custom_list.setSpacing(4); self._custom_list.setContentsMargins(0,0,0,0)
        c2.addLayout(self._custom_list)

        btn_new = QPushButton("✚  Créer un thème personnalisé")
        btn_new.setFixedHeight(30)
        btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_new.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};"
            f"border:1px dashed {T.BORDER2};border-radius:6px;"
            f"font-size:9pt;font-weight:600;}}"
            f"QPushButton:hover{{color:{T.TEXT};border-color:{T.ORANGE};}}")
        btn_new.clicked.connect(self._new_custom)
        c2.addWidget(btn_new)

        lay.addWidget(card2)
        lay.addStretch()
        scroll.setWidget(inner)
        root.addWidget(scroll)

        self._refresh_custom_list()
        self._refresh_theme_btns()

    # ── Thèmes intégrés ──────────────────────────────────────────────

    def _apply_builtin(self, key: str):
        cfg = model.load_config()
        cfg["theme_name"] = key
        cfg["dark_theme"] = key in ("sombre", "retro_dark")
        model.save_config(cfg)
        self._ask_restart()

    def _ask_restart(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Thème")
        dlg.setFixedWidth(280)
        dlg.setStyleSheet(
            f"QDialog{{background:{T.BG};color:{T.TEXT};}}"
            f"QLabel{{background:transparent;color:{T.TEXT};font-size:9pt;}}"
            f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};"
            f"border:1px solid {T.BORDER};border-radius:6px;"
            f"padding:5px 14px;font-size:9pt;font-weight:600;}}"
            f"QPushButton:hover{{background:{T.BORDER};color:{T.TEXT};}}")
        lay = QVBoxLayout(dlg); lay.setContentsMargins(16,14,16,14); lay.setSpacing(12)
        msg = QLabel("Le thème sera appliqué au prochain démarrage.\nRedémarrer maintenant ?")
        msg.setWordWrap(True)
        lay.addWidget(msg)
        btn_row = QHBoxLayout(); btn_row.setSpacing(8); btn_row.addStretch()
        btn_later = QPushButton("Plus tard")
        btn_later.setFixedHeight(30)
        btn_later.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_later.clicked.connect(dlg.reject)
        btn_now = QPushButton("Redémarrer")
        btn_now.setFixedHeight(30)
        btn_now.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_now.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});"
            f"color:white;border:none;border-radius:6px;"
            f"font-size:9pt;font-weight:700;}}")
        btn_now.clicked.connect(dlg.accept)
        for b in (btn_later, btn_now):
            btn_row.addWidget(b)
        lay.addLayout(btn_row)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._restart_app()

    def _restart_app(self):
        import sys, os
        from PySide6.QtWidgets import QApplication
        QApplication.instance().quit()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def _refresh_theme_btns(self):
        cfg    = model.load_config()
        active = cfg.get("theme_name", "")
        on_ss  = (
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});"
            f"color:white;border:none;border-radius:6px;"
            f"font-size:8pt;font-weight:700;}}")
        off_ss = (
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
            f"border:1px solid {T.BORDER};border-radius:6px;"
            f"font-size:8pt;font-weight:600;}}"
            f"QPushButton:hover{{color:{T.TEXT};}}")
        for key, btn in self._theme_btns.items():
            btn.setStyleSheet(on_ss if key == active else off_ss)

    # ── Thèmes personnalisés ──────────────────────────────────────────

    def _refresh_custom_list(self):
        while self._custom_list.count():
            item = self._custom_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cfg     = model.load_config()
        customs = cfg.get("custom_themes", {})
        active  = cfg.get("theme_name", "")

        for name, palette in customs.items():
            is_active = (active == f"custom:{name}")
            accent    = palette.get("GRAD1", "#888")

            row = QHBoxLayout(); row.setSpacing(6); row.setContentsMargins(0,0,0,0)

            dot = QFrame()
            dot.setFixedSize(12, 12)
            dot.setStyleSheet(
                f"QFrame{{background:{accent};border-radius:6px;border:none;}}")
            row.addWidget(dot)

            lbl = QLabel(name)
            lbl.setStyleSheet(
                f"font-size:9pt;font-weight:{'700' if is_active else '400'};"
                f"color:{T.ORANGE if is_active else T.TEXT};background:transparent;")
            row.addWidget(lbl, 1)

            btn_apply = QPushButton("Appliquer")
            btn_apply.setFixedHeight(24)
            btn_apply.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            btn_apply.setMinimumWidth(62)
            btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_apply.clicked.connect(lambda _, n=name, p=palette: self._apply_custom(n, p))
            row.addWidget(btn_apply)

            btn_edit = QPushButton("Éditer")
            btn_edit.setFixedHeight(24)
            btn_edit.setMinimumWidth(48)
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.clicked.connect(lambda _, n=name, p=palette: self._open_editor(n, p))
            row.addWidget(btn_edit)

            btn_del = QPushButton("Supp.")
            btn_del.setFixedHeight(24)
            btn_del.setMinimumWidth(44)
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setStyleSheet(
                f"QPushButton{{background:transparent;color:{T.RED};"
                f"border:1px solid {T.RED};border-radius:5px;"
                f"font-size:8pt;font-weight:600;}}"
                f"QPushButton:hover{{background:{T.RED};color:white;}}")
            btn_del.clicked.connect(lambda _, n=name: self._delete_custom(n))
            row.addWidget(btn_del)

            w = QWidget(); w.setLayout(row)
            self._custom_list.addWidget(w)

    def _new_custom(self):
        name, ok = _input_dialog(self, "Nouveau thème", "Nom du thème :")
        if not ok or not name.strip():
            return
        name = name.strip()
        cfg  = model.load_config()
        customs = cfg.get("custom_themes", {})
        if name in customs:
            _warn_dialog(self, "Erreur", f"Un thème « {name} » existe déjà.")
            return
        base = dict(theme.get_active_palette())
        self._open_editor(name, base, is_new=True)

    def _open_editor(self, name: str, palette: dict, is_new: bool = False):
        dlg = ThemeEditorDialog(name, palette, parent=self)
        if dlg.exec():
            if dlg.saved:
                cfg     = model.load_config()
                customs = cfg.get("custom_themes", {})
                customs[name]        = dlg.result_palette
                cfg["custom_themes"] = customs
                cfg["theme_name"]    = f"custom:{name}"
                model.save_config(cfg)
                self._refresh_custom_list()
                self._refresh_theme_btns()
                self._ask_restart()
        elif is_new:
            pass  # annulé, rien à sauvegarder

    def _apply_custom(self, name: str, palette: dict):
        cfg = model.load_config()
        cfg["theme_name"] = f"custom:{name}"
        model.save_config(cfg)
        self._refresh_custom_list()
        self._refresh_theme_btns()
        self._ask_restart()

    def _delete_custom(self, name: str):
        cfg     = model.load_config()
        customs = cfg.get("custom_themes", {})
        customs.pop(name, None)
        cfg["custom_themes"] = customs
        if cfg.get("theme_name") == f"custom:{name}":
            cfg["theme_name"] = "sombre"
        model.save_config(cfg)
        self._refresh_custom_list()
        self._refresh_theme_btns()

    def update_path(self, p):
        self._path_lbl.setText(p)

    def _refresh_dnd_status(self):
        try:
            from os_bridge import focus_assist
            active = focus_assist.is_dnd_active()
        except Exception:
            active = None
        if active is None:
            self._dnd_status_lbl.setText("⚪  Détection indisponible sur ce système.")
        elif active:
            self._dnd_status_lbl.setText(
                "🔴  Mode Ne pas déranger ACTIF — les notifications de jeu "
                "risquent d'être masquées.")
        else:
            self._dnd_status_lbl.setText(
                "🟢  Notifications Windows actives — tout est normal.")
