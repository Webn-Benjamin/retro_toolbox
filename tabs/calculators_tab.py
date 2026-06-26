"""tabs/calculators_tab.py — Onglet Calculateurs (menu + sous-calculateurs)."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QStackedWidget
)
from PySide6.QtCore import Qt, QTimer, QSize
import theme
from tabs.xp_metier_tab import XpMetierTab
from tabs.craft_hdv_tab import CraftHdvTab

T = theme


def _lbl(txt, color=None, size="9pt", bold=False):
    l = QLabel(txt)
    ss = f"background:transparent;font-size:{size};"
    if color: ss += f"color:{color};"
    if bold:  ss += "font-weight:bold;"
    l.setStyleSheet(ss)
    return l


class _Menu(QWidget):
    """Page d'accueil : liste des calculateurs disponibles."""

    def __init__(self, on_xp, on_craft, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet(
            f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});border:none;}}"
            f"QLabel{{background:transparent;color:white;border:none;}}")
        hdr.setFixedHeight(44)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(14, 0, 12, 0)
        t = QLabel("🧮  Calculateurs")
        t.setStyleSheet("font-size:11pt;font-weight:bold;color:white;background:transparent;")
        hl.addWidget(t)
        hl.addStretch()
        lay.addWidget(hdr)

        # Contenu
        body = QFrame()
        body.setStyleSheet(f"QFrame{{background:{T.BG};border:none;}}")
        cl = QVBoxLayout(body)
        cl.setContentsMargins(14, 14, 14, 14)
        cl.setSpacing(10)
        cl.addWidget(_lbl("Choisissez un calculateur :", T.SUBTEXT, "9pt"))

        for icon, title, subtitle, callback in [
            ("🎓", "Calculateur XP Métier",
             "Crafts nécessaires pour monter votre métier d'un niveau à un autre.",
             on_xp),
            ("🔧", "Calculateur Craft / HDV",
             "Marge et rentabilité d'un craft avec détection auto des ressources.",
             on_craft),
        ]:
            cl.addWidget(self._make_button(icon, title, subtitle, callback))

        lay.addWidget(body)
        lay.addStretch()

    def _make_button(self, icon, title, subtitle, callback):
        btn = QFrame()
        btn.setFixedHeight(76)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:12px;}}"
            f"QLabel{{background:transparent;border:none;}}")
        bl = QHBoxLayout(btn)
        bl.setContentsMargins(14, 0, 14, 0)
        bl.setSpacing(12)

        ic = QLabel(icon)
        ic.setFixedWidth(30)
        ic.setStyleSheet("font-size:20pt;background:transparent;")
        bl.addWidget(ic)

        texts = QVBoxLayout()
        texts.setSpacing(2)
        texts.addWidget(_lbl(title, T.TEXT, "10pt", bold=True))
        sub = _lbl(subtitle, T.HINT, "8pt")
        sub.setWordWrap(True)
        texts.addWidget(sub)
        bl.addLayout(texts, 1)

        arrow = _lbl("›", T.ORANGE, "18pt", bold=True)
        bl.addWidget(arrow)

        btn.mousePressEvent = lambda e: callback()
        return btn

    def sizeHint(self):
        # header(44) + marges(28) + label(~20) + spacing + 2 boutons(76) + spacing
        return QSize(350, 44 + 28 + 22 + 10 + 76 + 10 + 76)

    def minimumSizeHint(self):
        return QSize(350, 100)


class _FitStack(QStackedWidget):
    """Stack qui se dimensionne au widget actif uniquement."""
    def sizeHint(self):
        w = self.currentWidget()
        return w.sizeHint() if w else super().sizeHint()
    def minimumSizeHint(self):
        w = self.currentWidget()
        return w.minimumSizeHint() if w else super().minimumSizeHint()


class CalculatorsTab(QWidget):
    PAGE_MENU  = 0
    PAGE_XP    = 1
    PAGE_CRAFT = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._stack = _FitStack()

        self._menu = _Menu(
            on_xp=lambda: self._go(self.PAGE_XP),
            on_craft=lambda: self._go(self.PAGE_CRAFT),
        )
        self._xp    = XpMetierTab(on_back=lambda: self._go(self.PAGE_MENU))
        self._craft = CraftHdvTab(on_back=lambda: self._go(self.PAGE_MENU))

        self._stack.addWidget(self._menu)
        self._stack.addWidget(self._xp)
        self._stack.addWidget(self._craft)

        lay.addWidget(self._stack)
        self._stack.setCurrentIndex(self.PAGE_MENU)

    def _go(self, page: int):
        if hasattr(self._craft, "set_active"):
            self._craft.set_active(page == self.PAGE_CRAFT)
        self._stack.setCurrentIndex(page)
        QTimer.singleShot(0, self._adjust)

    def _adjust(self):
        cur = self._stack.currentWidget()
        if cur:
            sh = cur.sizeHint()
            if sh.isValid() and sh.height() > 0:
                self._stack.setFixedHeight(sh.height())
        w = self
        while w:
            w.updateGeometry()
            w = w.parentWidget()
        root = self.window()
        if not root:
            return
        root.setMinimumHeight(0)
        root.setMaximumHeight(16777215)
        root.adjustSize()
        if cur:
            # libérer le stack pour les futurs changements
            self._stack.setMinimumHeight(0)
            self._stack.setMaximumHeight(16777215)

    def sizeHint(self):
        return self._stack.currentWidget().sizeHint()

    def minimumSizeHint(self):
        return self._stack.currentWidget().minimumSizeHint()

    def set_active(self, active: bool):
        if not active and hasattr(self._craft, "set_active"):
            self._craft.set_active(False)
