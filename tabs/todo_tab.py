"""tabs/todo_tab.py — Todo list avec mise en forme."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QTextEdit, QSizePolicy, QApplication, QLabel
)
from PySide6.QtCore import Qt, QTimer, QSize, QSizeF
from PySide6.QtGui import QTextCharFormat, QFont, QColor
import model, theme

T = theme
CFG_KEY = "todo_content"


def _tbtn(text, tooltip, callback, checkable=False):
    b = QPushButton(text)
    b.setToolTip(tooltip)
    b.setFixedSize(28, 28)
    b.setCheckable(checkable)
    b.setStyleSheet(
        f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};"
        f"border:1px solid {T.BORDER};border-radius:3px;"
        f"font-size:10pt;font-weight:bold;padding:0;}}"
        f"QPushButton:hover{{background:{T.SURFACE};border-color:{T.ORANGE};color:{T.TEXT};}}"
        f"QPushButton:checked{{background:{T.ORANGE};color:white;border-color:{T.ORANGE};}}")
    b.clicked.connect(callback)
    return b


# ── AutoResizeEditor ───────────────────────────────────────
# QTextEdit qui grandit/rétrécit automatiquement avec son contenu

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
        # Forcer le layout avec la bonne largeur
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
        # Recalculer après affichage (viewport a la bonne taille)
        QTimer.singleShot(0, self._update_height)


# ── TodoTab ────────────────────────────────────────────────

class TodoTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self._build()
        self._load()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)

        # ── Barre d'outils — 2 lignes ─────────────────────
        toolbar = QFrame()
        toolbar.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:4px;}}")
        tb_main = QVBoxLayout(toolbar)
        tb_main.setContentsMargins(6, 5, 6, 5); tb_main.setSpacing(4)

        # Ligne 1 : formatage + taille + effacer
        row1 = QHBoxLayout(); row1.setSpacing(3)

        self._btn_bold   = _tbtn("B", "Gras",      self._toggle_bold,   checkable=True)
        self._btn_italic = _tbtn("I", "Italique",   self._toggle_italic, checkable=True)
        self._btn_under  = _tbtn("U", "Souligné",   self._toggle_under,  checkable=True)
        self._btn_bold.setStyleSheet(
            self._btn_bold.styleSheet() + "QPushButton{font-weight:900;}")
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

        for size, label in [(10,"S"),(13,"M"),(16,"L")]:
            b = QPushButton(label); b.setFixedSize(28,28)
            b.setToolTip(f"Taille {size}pt")
            b.setStyleSheet(
                f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};"
                f"border:1px solid {T.BORDER};border-radius:3px;"
                f"font-size:{size-2}pt;padding:0;}}"
                f"QPushButton:hover{{background:{T.SURFACE};border-color:{T.ORANGE};color:{T.TEXT};}}")
            b.clicked.connect(lambda _, s=size: self._set_size(s))
            row1.addWidget(b)

        row1.addStretch()
        btn_clear = QPushButton("✕"); btn_clear.setFixedSize(24,24)
        btn_clear.setToolTip("Effacer tout")
        btn_clear.setStyleSheet(
            f"QPushButton{{background:transparent;color:{T.HINT};"
            f"border:none;font-size:9pt;padding:0;}}"
            f"QPushButton:hover{{color:{T.RED};}}")
        btn_clear.clicked.connect(self._clear)
        row1.addWidget(btn_clear)
        tb_main.addLayout(row1)

        # Séparateur
        hsep = QFrame(); hsep.setFrameShape(QFrame.Shape.HLine)
        hsep.setStyleSheet(f"color:{T.BORDER};"); hsep.setFixedHeight(1)
        tb_main.addWidget(hsep)

        # Ligne 2 : couleurs avec bouton actif visible
        row2 = QHBoxLayout(); row2.setSpacing(4)

        self._color_btns = {}
        self._active_color = T.TEXT
        COLORS = [
            (T.TEXT,   "Normal",  "Aa"),
            (T.ORANGE, "Orange",  "Aa"),
            (T.GREEN,  "Vert",    "Aa"),
            (T.RED,    "Rouge",   "Aa"),
            (T.BLUE,   "Bleu",    "Aa"),
        ]
        for color, name, label in COLORS:
            b = QPushButton(label)
            b.setFixedSize(32, 24)
            b.setToolTip(name)
            b.setStyleSheet(
                f"QPushButton{{background:{T.BG_DARK};color:{color};"
                f"border:2px solid {T.BG_DARK};border-radius:3px;"
                f"font-size:9pt;font-weight:bold;padding:0;}}"
                f"QPushButton:hover{{border-color:{color};}}")
            b.clicked.connect(lambda _, col=color: self._set_color(col))
            row2.addWidget(b)
            self._color_btns[color] = b

        row2.addStretch()
        tb_main.addLayout(row2)
        lay.addWidget(toolbar)

        # Activer la couleur par défaut
        self._update_color_btn(T.TEXT)

        # ── Éditeur auto-resize ───────────────────────────
        self._editor = AutoResizeEditor()
        self._editor.setPlaceholderText(
            "Écris ta todo list ici...\n\n"
            "• Farmer les scaras\n"
            "• Acheter des runes PA\n"
            "• Mettre le set à jour")
        self._editor.setStyleSheet(
            f"QTextEdit{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:4px;padding:8px;color:{T.TEXT};font-size:11pt;}}"
            f"QTextEdit:focus{{border-color:{T.ORANGE};}}")
        # Propager le changement de hauteur à la fenêtre
        self._editor.document().contentsChanged.connect(self._propagate)
        self._editor.cursorPositionChanged.connect(self._update_toolbar)
        lay.addWidget(self._editor)

    # ── Formatage ─────────────────────────────────────────

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
        # Appliquer à la sélection ET au format courant du curseur
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
                    f"border:2px solid {color};border-radius:3px;"
                    f"font-size:9pt;font-weight:bold;padding:0;}}"
                    f"QPushButton:hover{{border-color:{color};}}")
            else:
                btn.setStyleSheet(
                    f"QPushButton{{background:{T.BG_DARK};color:{color};"
                    f"border:2px solid {T.BG_DARK};border-radius:3px;"
                    f"font-size:9pt;font-weight:bold;padding:0;}}"
                    f"QPushButton:hover{{border-color:{color};}}")

    def _update_toolbar(self):
        fmt = self._editor.textCursor().charFormat()
        self._btn_bold.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        self._btn_italic.setChecked(fmt.fontItalic())
        self._btn_under.setChecked(fmt.fontUnderline())
        # Mettre à jour la couleur active selon le curseur
        fg = fmt.foreground()
        if fg.style() != Qt.BrushStyle.NoBrush:
            col = fg.color().name().upper()
            # Chercher la couleur correspondante
            for color in self._color_btns:
                if QColor(color).name().upper() == col:
                    self._update_color_btn(color)
                    return

    def _clear(self):
        self._editor.clear()

    # ── Persistance ───────────────────────────────────────

    def _on_change(self):
        model.save_config({CFG_KEY: self._editor.toHtml()})

    def _load(self):
        content = model.load_config().get(CFG_KEY, "")
        if content:
            self._editor.setHtml(content)
        self._editor.textChanged.connect(self._on_change)

    # ── Propagation hauteur → fenêtre ─────────────────────

    def _propagate(self):
        """Remonte updateGeometry à travers tous les parents."""
        QTimer.singleShot(0, self._do_propagate)

    def _do_propagate(self):
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
        if not hasattr(self, '_editor'): return QSize(330, 200)
        editor_h = self._editor.sizeHint().height()
        lay = self.layout()
        m = lay.contentsMargins()
        return QSize(330,
                     m.top() + 38 + lay.spacing() + editor_h + m.bottom())
