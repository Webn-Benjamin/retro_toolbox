"""tabs/todo_tab.py — Notes multi-notes avec autosave."""

from __future__ import annotations
import uuid
from datetime import date

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QTextEdit, QSizePolicy, QApplication,
    QLabel, QLineEdit, QMessageBox, QScrollArea,
)
from PySide6.QtCore import Qt, QTimer, QSize, QSizeF
from PySide6.QtGui import QTextCharFormat, QFont, QColor
import model, theme

T = theme

AUTOSAVE_MS   = 3000   # délai autosave après frappe
MIGRATION_KEY = "todo_content"
NOTES_KEY     = "notes"
ACTIVE_KEY    = "notes_active_id"


# ── Helpers ────────────────────────────────────────────────

def _tbtn(text, tooltip, callback, checkable=False):
    b = QPushButton(text)
    b.setToolTip(tooltip)
    b.setFixedSize(28, 28)
    b.setCheckable(checkable)
    b.setStyleSheet(
        f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};"
        f"border:1px solid {T.BORDER};border-radius:6px;"
        f"font-size:10pt;font-weight:bold;padding:0;}}"
        f"QPushButton:hover{{background:{T.SURFACE};border-color:{T.ORANGE};color:{T.TEXT};}}"
        f"QPushButton:checked{{background:{T.ORANGE};color:white;border-color:{T.ORANGE};}}")
    b.clicked.connect(callback)
    return b


def _make_note(name: str, content: str = "") -> dict:
    return {
        "id":      f"n_{uuid.uuid4().hex[:8]}",
        "name":    name,
        "content": content,
        "updated": str(date.today()),
    }


# ── AutoResizeEditor ───────────────────────────────────────

class AutoResizeEditor(QTextEdit):
    """QTextEdit sans scroll qui se redimensionne selon le contenu."""

    MIN_H = 100

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.document().contentsChanged.connect(self._update_height)
        self.document().documentLayout().documentSizeChanged.connect(
            lambda _: self._update_height())

    def _get_doc_height(self) -> int:
        doc = self.document()
        w = self.viewport().width()
        if w < 10: w = 310
        doc.setPageSize(QSizeF(w, 16777215))
        return int(doc.size().height())

    def _update_height(self):
        h = self._get_doc_height()
        new_h = max(h + 16, self.MIN_H)
        if self.height() != new_h:
            self.setFixedHeight(new_h)
            self.updateGeometry()

    def sizeHint(self):
        h = self._get_doc_height()
        return QSize(self.width() or 310, max(h + 16, self.MIN_H))

    def showEvent(self, e):
        super().showEvent(e)
        QTimer.singleShot(0, self._update_height)


# ── TodoTab (alias NotesTab) ───────────────────────────────

class TodoTab(QWidget):
    """Onglet Notes multi-notes avec autosave."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self._notes:      list  = []
        self._active_id:  str | None = None
        self._dirty:      bool  = False
        self._panel_visible: bool = False
        self._migration_banner_shown: bool = False

        # Timer autosave
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(AUTOSAVE_MS)
        self._autosave_timer.timeout.connect(self._autosave)

        self._build()
        self._load_notes()

    # ── Construction UI ────────────────────────────────────

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)

        # ── Bouton "Mes notes" ─────────────────────────────
        self._btn_panel = QPushButton("📋  Mes notes")
        self._btn_panel.setFixedHeight(34)
        self._btn_panel.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_panel.clicked.connect(self._toggle_panel)
        self._style_panel_btn(False)
        lay.addWidget(self._btn_panel)

        # ── Bandeau autosave ───────────────────────────────
        self._save_banner = QLabel("● Sauvegardé")
        self._save_banner.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._save_banner.setFixedHeight(28)
        self._save_banner.setContentsMargins(10, 0, 10, 0)
        self._save_banner.setStyleSheet(
            f"QLabel{{background:#eafaf1;color:{T.GREEN};"
            f"border:1px solid {T.GREEN};border-radius:6px;"
            f"font-size:8pt;font-weight:bold;}}")
        lay.addWidget(self._save_banner)

        # ── Panel notes (caché par défaut) ─────────────────
        self._notes_panel = self._build_notes_panel()
        self._notes_panel.hide()
        lay.addWidget(self._notes_panel)

        # ── Barre d'outils ─────────────────────────────────
        toolbar = QFrame()
        toolbar.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:4px;}}")
        tb_main = QVBoxLayout(toolbar)
        tb_main.setContentsMargins(6, 5, 6, 5); tb_main.setSpacing(4)

        row1 = QHBoxLayout(); row1.setSpacing(3)
        self._btn_bold   = _tbtn("B", "Gras",      self._toggle_bold,   checkable=True)
        self._btn_italic = _tbtn("I", "Italique",   self._toggle_italic, checkable=True)
        self._btn_under  = _tbtn("U", "Souligné",   self._toggle_under,  checkable=True)
        self._btn_bold.setStyleSheet(
            self._btn_bold.styleSheet() + "QPushButton{font-weight:bold;}")
        self._btn_italic.setStyleSheet(
            self._btn_italic.styleSheet() + "QPushButton{font-style:italic;}")
        self._btn_under.setStyleSheet(
            self._btn_under.styleSheet() + "QPushButton{text-decoration:underline;}")
        row1.addWidget(self._btn_bold)
        row1.addWidget(self._btn_italic)
        row1.addWidget(self._btn_under)

        v1 = QFrame(); v1.setFrameShape(QFrame.Shape.VLine)
        v1.setStyleSheet(f"color:{T.BORDER};"); v1.setFixedWidth(1)
        row1.addWidget(v1)

        for size, label in [(10, "S"), (13, "M"), (16, "L")]:
            b = QPushButton(label); b.setFixedSize(28, 28)
            b.setToolTip(f"Taille {size}pt")
            b.setStyleSheet(
                f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};"
                f"border:1px solid {T.BORDER};border-radius:6px;"
                f"font-size:{size - 2}pt;padding:0;}}"
                f"QPushButton:hover{{background:{T.SURFACE};border-color:{T.ORANGE};color:{T.TEXT};}}")
            b.clicked.connect(lambda _, s=size: self._set_size(s))
            row1.addWidget(b)

        row1.addStretch()
        btn_clear = QPushButton("✕"); btn_clear.setFixedSize(24, 24)
        btn_clear.setToolTip("Effacer tout")
        btn_clear.setStyleSheet(
            f"QPushButton{{background:transparent;color:{T.HINT};"
            f"border:none;font-size:9pt;padding:0;}}"
            f"QPushButton:hover{{color:{T.RED};}}")
        btn_clear.clicked.connect(self._clear)
        row1.addWidget(btn_clear)
        tb_main.addLayout(row1)

        hsep = QFrame(); hsep.setFrameShape(QFrame.Shape.HLine)
        hsep.setStyleSheet(f"color:{T.BORDER};"); hsep.setFixedHeight(1)
        tb_main.addWidget(hsep)

        row2 = QHBoxLayout(); row2.setSpacing(4)
        self._color_btns = {}
        self._active_color = T.TEXT
        COLORS = [
            (T.TEXT,   "Normal", "Aa"),
            (T.ORANGE, "Orange", "Aa"),
            (T.GREEN,  "Vert",   "Aa"),
            (T.RED,    "Rouge",  "Aa"),
            (T.BLUE,   "Bleu",   "Aa"),
        ]
        for color, name, label in COLORS:
            b = QPushButton(label); b.setFixedSize(32, 24); b.setToolTip(name)
            b.setStyleSheet(
                f"QPushButton{{background:{T.BG_DARK};color:{color};"
                f"border:2px solid {T.BG_DARK};border-radius:6px;"
                f"font-size:9pt;font-weight:bold;padding:0;}}"
                f"QPushButton:hover{{border-color:{color};}}")
            b.clicked.connect(lambda _, col=color: self._set_color(col))
            row2.addWidget(b)
            self._color_btns[color] = b

        vsep = QFrame(); vsep.setFrameShape(QFrame.Shape.VLine)
        vsep.setStyleSheet(f"color:{T.BORDER};"); vsep.setFixedWidth(1)
        row2.addWidget(vsep)

        btn_cb = QPushButton("☐"); btn_cb.setFixedSize(28, 24)
        btn_cb.setToolTip("Insérer une case à cocher")
        btn_cb.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.TEXT};"
            f"border:1px solid {T.BORDER};border-radius:6px;font-size:13pt;padding:0;}}"
            f"QPushButton:hover{{border-color:{T.ORANGE};color:{T.ORANGE};}}")
        btn_cb.clicked.connect(self._insert_checkbox)
        row2.addWidget(btn_cb)

        btn_reset_cb = QPushButton("↺☐"); btn_reset_cb.setFixedSize(36, 24)
        btn_reset_cb.setToolTip("Tout décocher")
        btn_reset_cb.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
            f"border:1px solid {T.BORDER};border-radius:6px;font-size:8pt;font-weight:bold;padding:0;}}"
            f"QPushButton:hover{{border-color:{T.ORANGE};color:{T.TEXT};}}")
        btn_reset_cb.clicked.connect(self._reset_checkboxes)
        row2.addWidget(btn_reset_cb)
        row2.addStretch()
        tb_main.addLayout(row2)
        lay.addWidget(toolbar)
        self._update_color_btn(T.TEXT)

        # ── Éditeur ────────────────────────────────────────
        self._editor = AutoResizeEditor()
        self._editor.setPlaceholderText(
            "Écris ta note ici...\n\n"
            "• Farmer les scaras\n"
            "• Acheter des runes PA\n"
            "• Mettre le set à jour")
        self._editor.setStyleSheet(
            f"QTextEdit{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:4px;padding:8px;color:{T.TEXT};font-size:11pt;}}"
            f"QTextEdit:focus{{border-color:{T.ORANGE};}}")
        self._editor.document().contentsChanged.connect(self._propagate)
        self._editor.cursorPositionChanged.connect(self._update_toolbar)
        orig_mouse = self._editor.mousePressEvent
        def _mouse(e, _orig=orig_mouse):
            _orig(e); self._maybe_toggle_checkbox(e)
        self._editor.mousePressEvent = _mouse
        lay.addWidget(self._editor)

    def _build_notes_panel(self) -> QFrame:
        """Construit le panel liste des notes (style PuitPanel)."""
        panel = QFrame()
        panel.setStyleSheet(
            f"QFrame{{background:{T.SURFACE2};border:1px solid {T.BORDER};"
            f"border-radius:10px;}}"
            f"QFrame QLabel{{background:transparent;border:none;}}"
            f"QFrame QPushButton{{border:none;}}")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(12, 10, 12, 10); lay.setSpacing(8)

        # Champ nom de la note
        self._note_name_edit = QLineEdit()
        self._note_name_edit.setPlaceholderText("Nom de la note…")
        self._note_name_edit.setFixedHeight(32)
        self._note_name_edit.setStyleSheet(
            f"QLineEdit{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:8px;padding:0 10px;font-size:11pt;font-weight:bold;color:{T.TEXT};}}"
            f"QLineEdit:focus{{border-color:{T.ORANGE};}}")
        lay.addWidget(self._note_name_edit)

        # Boutons actions
        btn_row = QHBoxLayout(); btn_row.setSpacing(7)

        self._btn_new = QPushButton("＋ Nouvelle note")
        self._btn_new.setFixedHeight(32)
        self._btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_new.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
            f"border-radius:8px;font-size:8.5pt;font-weight:bold;padding:0 8px;}}"
            f"QPushButton:hover{{background:{T.GRAD2};}}")
        self._btn_new.clicked.connect(self._new_note)
        btn_row.addWidget(self._btn_new)

        self._btn_save = QPushButton("💾 Enregistrer")
        self._btn_save.setFixedHeight(32)
        self._btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_save.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};"
            f"border:1px solid {T.BORDER};border-radius:8px;"
            f"font-size:8.5pt;font-weight:bold;padding:0 8px;}}"
            f"QPushButton:hover{{border-color:{T.GREEN};color:{T.GREEN};}}")
        self._btn_save.clicked.connect(self._save_current)
        btn_row.addWidget(self._btn_save)

        self._btn_del = QPushButton("🗑 Supprimer")
        self._btn_del.setFixedHeight(32)
        self._btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_del.setStyleSheet(
            f"QPushButton{{background:rgba(229,57,53,.08);color:{T.RED};"
            f"border:1px solid rgba(229,57,53,.3);border-radius:8px;"
            f"font-size:8.5pt;font-weight:bold;padding:0 8px;}}"
            f"QPushButton:hover{{background:rgba(229,57,53,.18);}}")
        self._btn_del.clicked.connect(self._delete_note)
        btn_row.addWidget(self._btn_del)
        lay.addLayout(btn_row)

        # Séparateur
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{T.BORDER};"); sep.setFixedHeight(1)
        lay.addWidget(sep)

        # Titre liste
        lbl = QLabel("Notes enregistrées")
        lbl.setStyleSheet(
            f"font-size:9pt;font-weight:bold;color:{T.HINT};"
            f"text-transform:uppercase;letter-spacing:0.5px;")
        lay.addWidget(lbl)

        # Zone scrollable pour la liste
        self._notes_list_widget = QWidget()
        self._notes_list_widget.setStyleSheet("background:transparent;")
        self._notes_list_layout = QVBoxLayout(self._notes_list_widget)
        self._notes_list_layout.setContentsMargins(0, 0, 0, 0)
        self._notes_list_layout.setSpacing(5)
        self._notes_list_layout.addStretch()

        scroll = QScrollArea()
        scroll.setFixedHeight(130)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea{{background:transparent;border:none;}}"
            f"QScrollBar:vertical{{background:{T.BG_DARK};width:5px;border-radius:4px;}}"
            f"QScrollBar::handle:vertical{{background:{T.BORDER};border-radius:4px;min-height:15px;}}"
            f"QScrollBar::handle:vertical:hover{{background:{T.ORANGE};}}"
            f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        scroll.setWidget(self._notes_list_widget)
        lay.addWidget(scroll)

        return panel

    # ── Panel affichage ────────────────────────────────────

    def _toggle_panel(self):
        self._panel_visible = not self._panel_visible
        self._notes_panel.setVisible(self._panel_visible)
        self._style_panel_btn(self._panel_visible)
        if self._panel_visible:
            self._refresh_notes_list()
        self._propagate()

    def _style_panel_btn(self, active: bool):
        if active:
            self._btn_panel.setText("✕  Fermer")
            self._btn_panel.setStyleSheet(
                f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
                f"border-radius:8px;font-weight:bold;font-size:9pt;padding:7px 0;}}"
                f"QPushButton:hover{{background:{T.GRAD2};}}")
        else:
            self._btn_panel.setText("📋  Mes notes")
            self._btn_panel.setStyleSheet(
                f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};"
                f"border:1px solid {T.BORDER};border-radius:8px;"
                f"font-weight:bold;font-size:9pt;padding:7px 0;}}"
                f"QPushButton:hover{{border-color:{T.ORANGE};color:{T.ORANGE};}}")

    # ── Liste des notes ────────────────────────────────────

    def _refresh_notes_list(self):
        """Reconstruit les lignes de la liste des notes."""
        # Vider
        while self._notes_list_layout.count() > 1:
            item = self._notes_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for note in self._notes:
            row = self._make_note_row(note)
            self._notes_list_layout.insertWidget(
                self._notes_list_layout.count() - 1, row)

        # Mettre à jour le champ nom
        active = self._get_active_note()
        if active:
            self._note_name_edit.setText(active["name"])

    def _make_note_row(self, note: dict) -> QFrame:
        is_active = (note["id"] == self._active_id)
        row = QFrame()
        border_l = f"border-left:3px solid {T.GREEN};" if is_active else ""
        bg = "#eafaf1" if is_active else T.SURFACE
        name_col = T.GREEN if is_active else T.TEXT
        row.setStyleSheet(
            f"QFrame{{background:{bg};{border_l}border:1px solid {T.BORDER};"
            f"border-radius:9px;}}"
            f"QFrame:hover{{border-color:{T.GREEN};}}"
            f"QFrame QLabel{{background:transparent;border:none;}}")
        row.setCursor(Qt.CursorShape.PointingHandCursor)

        hl = QHBoxLayout(row); hl.setContentsMargins(10, 7, 10, 7); hl.setSpacing(8)
        ico = QLabel("📋"); ico.setStyleSheet("font-size:11px;")
        name_lbl = QLabel(note["name"])
        name_lbl.setStyleSheet(
            f"font-size:10.5pt;font-weight:{'700' if is_active else '600'};"
            f"color:{name_col};")
        date_lbl = QLabel(note.get("updated", ""))
        date_lbl.setStyleSheet(f"font-size:8pt;color:{T.HINT};")
        hl.addWidget(ico); hl.addWidget(name_lbl, 1); hl.addWidget(date_lbl)

        # Clic → changer de note
        row.mousePressEvent = lambda e, nid=note["id"]: self._request_switch(nid)
        return row

    # ── Chargement / sauvegarde ────────────────────────────

    def _load_notes(self):
        """Charge les notes depuis le config, migrate si nécessaire."""
        cfg = model.load_config()

        # Migration depuis l'ancien todo_content
        if NOTES_KEY not in cfg:
            old_content = cfg.get(MIGRATION_KEY, "")
            first_note = _make_note("Ma note", old_content)
            self._notes = [first_note]
            self._active_id = first_note["id"]
            self._persist()
            if old_content:
                self._migration_banner_shown = True
                self._show_banner("✅ Tes notes ont été migrées — rien n'a été perdu",
                                  "ok")
        else:
            self._notes = cfg.get(NOTES_KEY, [])
            self._active_id = cfg.get(ACTIVE_KEY)
            # Sécurité : si l'id actif n'existe plus
            ids = [n["id"] for n in self._notes]
            if self._active_id not in ids:
                self._active_id = self._notes[0]["id"] if self._notes else None

        # Charger le contenu de la note active dans l'éditeur
        self._load_active_into_editor()

        # Connecter le signal de changement APRÈS le chargement
        self._editor.textChanged.connect(self._on_text_changed)

    def _load_active_into_editor(self):
        """Met le contenu de la note active dans l'éditeur."""
        note = self._get_active_note()
        self._editor.blockSignals(True)
        if note and note.get("content"):
            self._editor.setHtml(note["content"])
        else:
            self._editor.clear()
        self._editor.blockSignals(False)
        self._dirty = False
        if not self._migration_banner_shown:
            name = note["name"] if note else "—"
            self._show_banner(f"● Sauvegardé — \"{name}\"", "ok")

    def _persist(self):
        """Écrit les notes dans le config."""
        model.save_config({
            NOTES_KEY:  self._notes,
            ACTIVE_KEY: self._active_id,
        })

    def _save_current(self, silent: bool = False):
        """Sauvegarde la note active (nom + contenu)."""
        note = self._get_active_note()
        if not note:
            return
        # Mettre à jour le nom si le panel est ouvert
        if self._panel_visible:
            new_name = self._note_name_edit.text().strip()
            if new_name:
                note["name"] = new_name
        note["content"] = self._editor.toHtml()
        note["updated"] = str(date.today())
        self._dirty = False
        self._persist()
        if not silent:
            self._show_banner(f"● Sauvegardé — \"{note['name']}\"", "ok")
            if self._panel_visible:
                self._refresh_notes_list()

    def _autosave(self):
        """Autosave silencieux déclenché par le timer."""
        note = self._get_active_note()
        if not note:
            # Pas de note active → créer "Note sans titre"
            new_note = _make_note("Note sans titre", self._editor.toHtml())
            self._notes.append(new_note)
            self._active_id = new_note["id"]
        else:
            note["content"] = self._editor.toHtml()
            note["updated"] = str(date.today())
        self._dirty = False
        self._persist()
        note = self._get_active_note()
        self._show_banner(f"● Sauvegardé — \"{note['name']}\"", "ok")
        if self._panel_visible:
            self._refresh_notes_list()

    # ── Actions notes ──────────────────────────────────────

    def _new_note(self):
        """Crée une nouvelle note vide et la rend active."""
        if self._dirty:
            self._save_current(silent=True)
        note = _make_note("Nouvelle note")
        self._notes.append(note)
        self._active_id = note["id"]
        self._persist()
        self._editor.blockSignals(True)
        self._editor.clear()
        self._editor.blockSignals(False)
        self._dirty = False
        self._note_name_edit.setText("Nouvelle note")
        self._refresh_notes_list()
        self._show_banner("● Nouvelle note créée", "ok")
        self._note_name_edit.setFocus()
        self._note_name_edit.selectAll()

    def _delete_note(self):
        """Supprime la note active après confirmation."""
        note = self._get_active_note()
        if not note:
            return
        if len(self._notes) == 1:
            QMessageBox.information(self, "Note",
                "Tu ne peux pas supprimer la dernière note.")
            return
        rep = QMessageBox.question(
            self, "Supprimer la note",
            f"Supprimer la note \"{note['name']}\" ?\nCette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if rep != QMessageBox.StandardButton.Yes:
            return
        self._notes = [n for n in self._notes if n["id"] != self._active_id]
        self._active_id = self._notes[0]["id"]
        self._persist()
        self._load_active_into_editor()
        self._refresh_notes_list()

    def _request_switch(self, note_id: str):
        """Demande de changer de note — confirme si modifié."""
        if note_id == self._active_id:
            return
        if self._dirty:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Note modifiée")
            note = self._get_active_note()
            dlg.setText(f"💾 Sauvegarder \"{note['name'] if note else ''}\" ?")
            dlg.setInformativeText(
                "Tu as des modifications non sauvegardées.")
            btn_save    = dlg.addButton("💾 Sauvegarder",
                                        QMessageBox.ButtonRole.AcceptRole)
            btn_ignore  = dlg.addButton("Ignorer",
                                        QMessageBox.ButtonRole.DestructiveRole)
            btn_cancel  = dlg.addButton("Annuler",
                                        QMessageBox.ButtonRole.RejectRole)
            dlg.setDefaultButton(btn_save)
            dlg.exec()
            clicked = dlg.clickedButton()
            if clicked == btn_cancel:
                return
            if clicked == btn_save:
                self._save_current(silent=True)
        self._active_id = note_id
        self._persist()
        self._load_active_into_editor()
        self._refresh_notes_list()

    # ── Événements éditeur ─────────────────────────────────

    def _on_text_changed(self):
        """Appelé à chaque frappe : marque dirty + (re)démarre autosave."""
        self._dirty = True
        self._show_banner(f"○ Sauvegarde dans {AUTOSAVE_MS // 1000}s…", "saving")
        self._autosave_timer.start()

    # ── Bandeau statut ─────────────────────────────────────

    def _show_banner(self, text: str, state: str):
        """Met à jour le bandeau autosave. state: ok | saving | error"""
        self._save_banner.setText(text)
        if state == "ok":
            self._save_banner.setStyleSheet(
                f"QLabel{{background:#eafaf1;color:{T.GREEN};"
                f"border:1px solid {T.GREEN};border-radius:6px;"
                f"font-size:8pt;font-weight:bold;padding:0 10px;}}")
        elif state == "saving":
            self._save_banner.setStyleSheet(
                f"QLabel{{background:#fff7ec;color:{T.ORANGE};"
                f"border:1px solid {T.ORANGE};border-radius:6px;"
                f"font-size:8pt;font-weight:bold;padding:0 10px;}}")
        else:
            self._save_banner.setStyleSheet(
                f"QLabel{{background:#fdecea;color:{T.RED};"
                f"border:1px solid {T.RED};border-radius:6px;"
                f"font-size:8pt;font-weight:bold;padding:0 10px;}}")

    # ── Helpers ────────────────────────────────────────────

    def _get_active_note(self) -> dict | None:
        for n in self._notes:
            if n["id"] == self._active_id:
                return n
        return None

    # ── Formatage ──────────────────────────────────────────

    def _toggle_bold(self):
        fmt = QTextCharFormat()
        cur = self._editor.textCursor().charFormat().fontWeight()
        fmt.setFontWeight(
            QFont.Weight.Normal if cur == QFont.Weight.Bold else QFont.Weight.Bold)
        self._editor.textCursor().mergeCharFormat(fmt)
        self._editor.setFocus()

    def _toggle_italic(self):
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self._editor.textCursor().charFormat().fontItalic())
        self._editor.textCursor().mergeCharFormat(fmt)
        self._editor.setFocus()

    def _toggle_under(self):
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self._editor.textCursor().charFormat().fontUnderline())
        self._editor.textCursor().mergeCharFormat(fmt)
        self._editor.setFocus()

    def _set_size(self, size):
        fmt = QTextCharFormat(); fmt.setFontPointSize(size)
        self._editor.textCursor().mergeCharFormat(fmt)
        self._editor.setFocus()

    def _set_color(self, color):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        self._editor.mergeCurrentCharFormat(fmt)
        self._active_color = color
        self._update_color_btn(color)
        self._editor.setFocus()

    def _update_color_btn(self, active_color):
        for color, btn in self._color_btns.items():
            if color == active_color:
                btn.setStyleSheet(
                    f"QPushButton{{background:{color};color:white;"
                    f"border:2px solid {color};border-radius:6px;"
                    f"font-size:9pt;font-weight:bold;padding:0;}}"
                    f"QPushButton:hover{{border-color:{color};}}")
            else:
                btn.setStyleSheet(
                    f"QPushButton{{background:{T.BG_DARK};color:{color};"
                    f"border:2px solid {T.BG_DARK};border-radius:6px;"
                    f"font-size:9pt;font-weight:bold;padding:0;}}"
                    f"QPushButton:hover{{border-color:{color};}}")

    def _update_toolbar(self):
        fmt = self._editor.textCursor().charFormat()
        self._btn_bold.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        self._btn_italic.setChecked(fmt.fontItalic())
        self._btn_under.setChecked(fmt.fontUnderline())
        fg = fmt.foreground()
        if fg.style() != Qt.BrushStyle.NoBrush:
            col = fg.color().name().upper()
            for color in self._color_btns:
                if QColor(color).name().upper() == col:
                    self._update_color_btn(color)
                    return

    def _clear(self):
        self._editor.clear()

    def _insert_checkbox(self):
        cursor = self._editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.EndOfLine)
        if self._editor.document().blockCount() > 1 or cursor.block().text().strip():
            cursor.insertBlock()
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(T.TEXT))
        cursor.setCharFormat(fmt)
        cursor.insertText("☐ ")
        self._editor.setTextCursor(cursor)
        self._editor.setFocus()

    def _maybe_toggle_checkbox(self, e):
        cursor = self._editor.cursorForPosition(e.pos())
        c2 = self._editor.textCursor()
        c2.setPosition(cursor.position())
        c2.movePosition(c2.MoveOperation.Right, c2.MoveMode.KeepAnchor, 1)
        ch = c2.selectedText()
        if ch in ("☐", "☑"):
            new_ch = "☑" if ch == "☐" else "☐"
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(T.GREEN if new_ch == "☑" else T.TEXT))
            c2.insertText(new_ch, fmt)
            self._editor.setTextCursor(c2)

    def _reset_checkboxes(self):
        doc = self._editor.document()
        cursor = self._editor.textCursor()
        cursor.beginEditBlock()
        c = doc.find("☑")
        while not c.isNull():
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(T.TEXT))
            c.insertText("☐", fmt)
            c = doc.find("☑")
        cursor.endEditBlock()
        self._editor.setFocus()

    # ── Propagation hauteur ────────────────────────────────

    def _propagate(self):
        QTimer.singleShot(0, self._do_propagate)

    def _do_propagate(self):
        def do():
            w = self
            while w:
                w.updateGeometry()
                w = w.parentWidget()
            root = self.window()
            if not root: return
            root.setMinimumHeight(0)
            root.setMaximumHeight(16777215)
            root.adjustSize()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, do)

    def sizeHint(self):
        if not hasattr(self, '_editor'):
            return QSize(330, 200)
        lay = self.layout()
        if not lay: return QSize(330, 200)
        h = lay.contentsMargins().top() + lay.contentsMargins().bottom()
        for i in range(lay.count()):
            item = lay.itemAt(i)
            if not item: continue
            w = item.widget()
            if w and w.isVisible():
                h += w.sizeHint().height() + lay.spacing()
            elif item.layout():
                h += item.layout().sizeHint().height() + lay.spacing()
        return QSize(330, max(h, 100))
