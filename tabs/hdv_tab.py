"""tabs/hdv_tab.py — Prix HDV communautaires (lecture + soumission).

UI :
  - sélecteur de serveur (boune / allisteria / fallanster)
  - champ de recherche dédié
  - filtre par catégorie (ressources / équipements / tous)
  - liste paginée avec chargement progressif au scroll
  - chaque ligne : item, prix médian, dernier modificateur, bouton signaler
  - bouton "Proposer un prix" avec autocomplete sur la liste connue
  - première utilisation : demande le pseudo (figé ensuite côté serveur)

Toute la logique réseau est dans hdv_prices.py et tourne dans des threads
pour ne jamais geler l'interface.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QScrollArea, QCompleter, QDialog, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QObject, QStringListModel, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QLinearGradient, QPainterPath, QFont
import theme
import hdv_prices as api

T = theme

PAGE_SIZE = 20   # nombre d'items chargés par "page" (scroll infini)


# ─── Helpers UI (mêmes conventions que les autres onglets) ────────────
def _lbl(txt, color=None, size="9pt", bold=False):
    l = QLabel(txt)
    ss = f"background:transparent;font-size:{size};"
    if color: ss += f"color:{color};"
    if bold:  ss += "font-weight:bold;"
    l.setStyleSheet(ss)
    return l

def _card():
    f = QFrame()
    f.setStyleSheet(
        f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};border-radius:12px;}}"
        f"QLabel{{background:transparent;border:none;}}")
    return f

def _fmt(v):
    try:
        return f"{int(v):,}".replace(",", " ")
    except Exception:
        return str(v)


def _time_ago(iso_str):
    """Convertit un timestamp ISO en 'il y a X' lisible."""
    if not iso_str:
        return "récemment"
    from datetime import datetime, timezone
    try:
        s = str(iso_str).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        secs = delta.total_seconds()
        if secs < 60:
            return "à l'instant"
        if secs < 3600:
            m = int(secs // 60)
            return f"il y a {m} min"
        if secs < 86400:
            h = int(secs // 3600)
            return f"il y a {h} h"
        d = int(secs // 86400)
        if d == 1:
            return "hier"
        if d < 30:
            return f"il y a {d} jours"
        mo = int(d // 30)
        return f"il y a {mo} mois"
    except Exception:
        return "récemment"


# ─── Worker réseau générique (thread) ─────────────────────────────────
class _Worker(QObject):
    done = Signal(object)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            res = self._fn(*self._args, **self._kwargs)
        except Exception as e:
            res = {"ok": False, "error": str(e)}
        self.done.emit(res)


def _run_async(parent, fn, on_done, *args, **kwargs):
    """Lance fn(*args) dans un thread, appelle on_done(result) dans l'UI."""
    thread = QThread(parent)
    worker = _Worker(fn, *args, **kwargs)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.done.connect(on_done)
    worker.done.connect(thread.quit)
    worker.done.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    # garder une réf pour éviter le GC
    if not hasattr(parent, "_threads"):
        parent._threads = []
    parent._threads.append(thread)
    thread.finished.connect(lambda: parent._threads.remove(thread)
                            if thread in parent._threads else None)
    thread.start()


# ─── Dialogue de saisie du pseudo (première utilisation) ──────────────
class _PseudoDialog(QDialog):
    def __init__(self, server, parent=None, current_pseudo=None, info_text=None):
        super().__init__(parent)
        self.setWindowTitle("Modifier ton pseudo" if current_pseudo else "Choisis ton pseudo")
        self.setFixedWidth(320)
        self.setStyleSheet(f"QDialog{{background:{T.BG};}}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        lay.addWidget(_lbl("Ton pseudo Dofus", T.TEXT, "11pt", bold=True))

        # Afficher le pseudo actuel s'il existe
        if current_pseudo:
            cur = QFrame()
            cur.setStyleSheet(
                f"QFrame{{background:{T.BG_DARK};border-radius:8px;border:none;}}"
                f"QLabel{{background:transparent;border:none;}}")
            cl = QHBoxLayout(cur)
            cl.setContentsMargins(10, 6, 10, 6)
            cl.setSpacing(6)
            cl.addWidget(_lbl("Pseudo actuel :", T.HINT, "8pt"))
            cl.addWidget(_lbl(current_pseudo, T.ORANGE, "10pt", bold=True))
            cl.addStretch()
            lay.addWidget(cur)

        info = _lbl(info_text or ("Il sera affiché à côté des prix que tu proposes. "
                    "Une fois choisi, il ne pourra plus être modifié."),
                    T.HINT, "8pt")
        info.setWordWrap(True)
        lay.addWidget(info)

        self._inp = QLineEdit()
        self._inp.setPlaceholderText("Nouveau pseudo (2 à 24 caractères)")
        self._inp.setFixedHeight(34)
        self._inp.setStyleSheet(
            f"QLineEdit{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:8px;padding:2px 10px;color:{T.TEXT};font-size:10pt;}}"
            f"QLineEdit:focus{{border:1px solid {T.ORANGE};}}")
        lay.addWidget(self._inp)

        btn = QPushButton("Valider")
        btn.setFixedHeight(36)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
            f"border-radius:8px;font-size:10pt;font-weight:bold;}}"
            f"QPushButton:hover{{background:{T.ORANGE_L}}};")
        btn.clicked.connect(self.accept)
        lay.addWidget(btn)

        self._server = server

    def pseudo(self):
        return self._inp.text().strip()


# ─── Onglet principal ─────────────────────────────────────────────────
class _ConfirmDialog(QDialog):
    """Boîte de confirmation stylisée (remplace QMessageBox illisible)."""
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(340)
        self.setStyleSheet(f"QDialog{{background:{T.BG};}}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        lay.addWidget(_lbl(title, T.TEXT, "12pt", bold=True))
        msg = _lbl(message, T.SUBTEXT, "9pt")
        msg.setWordWrap(True)
        lay.addWidget(msg)

        row = QHBoxLayout()
        row.setSpacing(8)
        no = QPushButton("Annuler")
        no.setFixedHeight(34)
        no.setCursor(Qt.CursorShape.PointingHandCursor)
        no.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};border:none;"
            f"border-radius:8px;font-size:9pt;font-weight:bold;}}"
            f"QPushButton:hover{{color:{T.TEXT}}};")
        no.clicked.connect(self.reject)
        row.addWidget(no)

        yes = QPushButton("Confirmer")
        yes.setFixedHeight(34)
        yes.setCursor(Qt.CursorShape.PointingHandCursor)
        yes.setStyleSheet(
            f"QPushButton{{background:{T.RED};color:white;border:none;"
            f"border-radius:8px;font-size:9pt;font-weight:bold;}}"
            f"QPushButton:hover{{background:#c62828}};")
        yes.clicked.connect(self.accept)
        row.addWidget(yes)
        lay.addLayout(row)


class _InfoDialog(QDialog):
    """Petit message stylisé avec un seul bouton OK."""
    def __init__(self, title, message, parent=None, accent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(320)
        self.setStyleSheet(f"QDialog{{background:{T.BG};}}")
        accent = accent or T.ORANGE
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(12)
        lay.addWidget(_lbl(title, accent, "12pt", bold=True))
        msg = _lbl(message, T.SUBTEXT, "9pt")
        msg.setWordWrap(True)
        lay.addWidget(msg)
        ok = QPushButton("OK")
        ok.setFixedHeight(34)
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
            f"border-radius:8px;font-size:9pt;font-weight:bold;}}")
        ok.clicked.connect(self.accept)
        lay.addWidget(ok)


def _info(parent, title, message, accent=None):
    _InfoDialog(title, message, parent, accent).exec()


class HdvTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._server   = api.SERVERS[0]
        self._all_rows = []      # tous les prix reçus du serveur
        self._filtered = []      # après recherche/filtre
        self._shown    = 0       # nb d'items actuellement affichés
        self._items_cache = []   # liste d'items pour autocomplete
        # Délai de changement de pseudo (lu depuis la config serveur, défaut 15j)
        self._pseudo_change_days = 15
        self._favorites = self._load_favorites()
        try:
            cfg = api.get_settings()
            if cfg.get("pseudo_change_days"):
                self._pseudo_change_days = int(float(cfg["pseudo_change_days"]))
        except Exception:
            pass
        self._build()
        self._load_prices()
        self._load_items()

    # ── Construction UI ──────────────────────────────────────────────
    def _build(self):
        # Tooltips lisibles (fond clair, texte noir) — sinon blanc sur blanc
        self.setStyleSheet(
            f"QToolTip{{background:{T.SURFACE};color:#0d2318;"
            f"border:1px solid {T.BORDER};border-radius:4px;padding:4px 8px;"
            f"font-size:8pt;}}")

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
        t = QLabel("💰  Prix HDV communautaires")
        t.setStyleSheet("font-size:11pt;font-weight:bold;color:white;background:transparent;")
        hl.addWidget(t)
        hl.addStretch()
        refresh = QPushButton("⟳")
        refresh.setFixedSize(32, 32)
        refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh.setToolTip("Rafraîchir")
        refresh.setStyleSheet(
            "QPushButton{background:rgba(255,255,255,40);color:white;border:none;"
            "border-radius:6px;font-size:13pt;font-weight:bold;padding:0;}"
            "QPushButton:hover{background:rgba(255,255,255,80);}")
        refresh.clicked.connect(self._load_prices)
        hl.addWidget(refresh)
        lay.addWidget(hdr)

        # Barre de contrôle (serveur + recherche + catégorie)
        ctrl = QFrame()
        ctrl.setStyleSheet(f"QFrame{{background:{T.BG};border:none;}}")
        cv = QVBoxLayout(ctrl)
        cv.setContentsMargins(12, 12, 12, 8)
        cv.setSpacing(8)

        # Ligne serveur + catégorie
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        self._server_cb = QComboBox()
        for s in api.SERVERS:
            self._server_cb.addItem(s.capitalize(), s)
        self._server_cb.setFixedHeight(32)
        self._server_cb.setStyleSheet(self._combo_style())
        self._server_cb.currentIndexChanged.connect(self._on_server_change)
        row1.addWidget(self._server_cb, 1)

        self._cat_cb = QComboBox()
        self._cat_cb.addItem("Tous", "all")
        self._cat_cb.addItem("Ressources", "resource")
        self._cat_cb.addItem("Équipements", "equipment")
        self._cat_cb.setFixedHeight(32)
        self._cat_cb.setStyleSheet(self._combo_style())
        self._cat_cb.currentIndexChanged.connect(lambda: self._apply_filter())
        row1.addWidget(self._cat_cb, 1)
        cv.addLayout(row1)

        # Ligne tri
        rowsort = QHBoxLayout()
        rowsort.setSpacing(8)
        rowsort.addWidget(_lbl("Trier :", T.HINT, "8pt"))
        self._sort_cb = QComboBox()
        for v, lab in [("recent", "Récemment mis à jour"),
                       ("name",   "Nom (A→Z)"),
                       ("price_asc",  "Prix ×1 croissant"),
                       ("price_desc", "Prix ×1 décroissant")]:
            self._sort_cb.addItem(lab, v)
        self._sort_cb.setFixedHeight(30)
        self._sort_cb.setStyleSheet(self._combo_style())
        self._sort_cb.currentIndexChanged.connect(lambda: self._apply_filter())
        rowsort.addWidget(self._sort_cb, 1)
        cv.addLayout(rowsort)

        # Champ de recherche dédié
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Rechercher une ressource / un item…")
        self._search.setFixedHeight(34)
        self._search.setStyleSheet(
            f"QLineEdit{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:8px;padding:2px 12px;color:{T.TEXT};font-size:10pt;}}"
            f"QLineEdit:focus{{border:1px solid {T.ORANGE};}}")
        self._search.textChanged.connect(self._on_search)
        cv.addWidget(self._search)

        # Bouton proposer un prix
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        add_btn = QPushButton("➕  Proposer un prix")
        add_btn.setFixedHeight(36)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
            f"border-radius:8px;font-size:9pt;font-weight:bold;}}"
            f"QPushButton:hover{{background:{T.ORANGE_L}}};")
        add_btn.clicked.connect(self._open_submit)
        btn_row.addWidget(add_btn)
        cv.addLayout(btn_row)

        # Bouton modifier pseudo (texte, pleine largeur, mention du délai)
        days = int(getattr(self, "_pseudo_change_days", 15))
        pseudo_btn = QPushButton(f"Modifier votre pseudo  ·  modifiable tous les {days} jours")
        pseudo_btn.setFixedHeight(32)
        pseudo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pseudo_btn.setStyleSheet(
            f"QPushButton{{background:{T.SURFACE};color:{T.SUBTEXT};"
            f"border:1px solid {T.BORDER};border-radius:8px;font-size:8pt;"
            f"font-weight:bold;}}"
            f"QPushButton:hover{{border-color:{T.ORANGE};color:{T.ORANGE};}}")
        pseudo_btn.clicked.connect(self._change_pseudo)
        cv.addWidget(pseudo_btn)

        self._fav_btn = QPushButton("⭐  Mes favoris")
        self._fav_btn.setFixedHeight(36)
        self._fav_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fav_btn.setStyleSheet(
            f"QPushButton{{background:{T.SURFACE};color:{T.GOLD};"
            f"border:1px solid {T.GOLD};border-radius:8px;font-size:9pt;"
            f"font-weight:bold;}}"
            f"QPushButton:hover{{background:{T.GOLD};color:white;}}")
        self._fav_btn.clicked.connect(self._toggle_fav_panel)
        cv.addWidget(self._fav_btn)

        # Panneau favoris dépliable (inline, sous le bouton)
        self._fav_panel = QFrame()
        self._fav_panel.setStyleSheet(
            f"QFrame{{background:{T.BG_DARK};border:1px solid {T.BORDER};"
            f"border-radius:8px;}}")
        self._fav_panel_lay = QVBoxLayout(self._fav_panel)
        self._fav_panel_lay.setContentsMargins(8, 8, 8, 8)
        self._fav_panel_lay.setSpacing(6)
        self._fav_panel.setVisible(False)
        cv.addWidget(self._fav_panel)

        lay.addWidget(ctrl)

        # Zone de liste scrollable (pagination au scroll)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet(f"QScrollArea{{background:{T.BG};}}")
        self._scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)

        self._list_container = QWidget()
        self._list_container.setStyleSheet(f"background:{T.BG};")
        self._list_lay = QVBoxLayout(self._list_container)
        self._list_lay.setContentsMargins(12, 4, 12, 12)
        self._list_lay.setSpacing(6)
        self._list_lay.addStretch()

        self._scroll.setWidget(self._list_container)
        lay.addWidget(self._scroll, 1)

        # État vide / chargement
        self._status = _lbl("Chargement des prix…", T.HINT, "9pt")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._list_lay.insertWidget(0, self._status)

    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(350, 760)

    def minimumSizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(350, 560)

    def _combo_style(self):
        return (
            f"QComboBox{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:8px;padding:2px 10px;color:{T.TEXT};font-size:9pt;}}"
            f"QComboBox:focus{{border:1px solid {T.ORANGE};}}"
            f"QComboBox::drop-down{{border:none;width:20px;}}"
            f"QComboBox QAbstractItemView{{background:{T.SURFACE};"
            f"color:{T.TEXT};selection-background-color:{T.BG_DARK};"
            f"border:1px solid {T.BORDER};}}")

    # ── Chargement des données ───────────────────────────────────────
    def _load_prices(self):
        self._status.setText(f"Chargement des prix ({self._server.capitalize()})…")
        self._status.setVisible(True)
        # Synchrone : la requête est rapide et c'est plus fiable que le thread
        QTimer.singleShot(50, lambda: self._on_prices_loaded(api.get_prices(self._server)))

    def _load_items(self):
        # liste d'items pour l'autocomplete (chargée une fois)
        def fetch():
            return api.search_items("", limit=2000) or []
        _run_async(self, fetch, self._on_items_loaded)

    def _on_items_loaded(self, items):
        if isinstance(items, list):
            self._items_cache = items

    def _on_prices_loaded(self, rows):
        if not isinstance(rows, list):
            self._status.setText("Impossible de charger les prix. Vérifie ta connexion.")
            self._status.setVisible(True)
            return
        self._all_rows = rows
        if not rows:
            self._status.setText(
                f"Aucun prix sur {self._server.capitalize()} pour le moment.\n"
                f"Sois le premier à en proposer un ! 💰")
            self._status.setVisible(True)
            self._clear_list()
            return
        self._apply_filter()

    # ── Recherche / filtre ───────────────────────────────────────────
    def _on_search(self):
        # léger debounce
        if hasattr(self, "_search_timer"):
            self._search_timer.stop()
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._apply_filter)
        self._search_timer.start(200)

    def _apply_filter(self):
        q = self._search.text().strip().lower()
        cat = self._cat_cb.currentData()
        rows = self._all_rows
        if q:
            rows = [r for r in rows if q in r.get("item_name", "").lower()]
        if cat and cat != "all":
            rows = [r for r in rows if r.get("category", "") == cat]
        rows = self._sort_rows(rows)
        self._filtered = rows
        self._shown = 0
        self._clear_list()
        if not rows:
            self._status.setText("Aucun résultat.")
            self._status.setVisible(True)
        else:
            self._status.setVisible(False)
            self._load_more()

    def _sort_rows(self, rows):
        mode = self._sort_cb.currentData() if hasattr(self, "_sort_cb") else "recent"
        def px1(r):
            v = r.get("median_x1")
            return v if v is not None else float("inf")
        if mode == "name":
            return sorted(rows, key=lambda r: r.get("item_name", "").lower())
        if mode == "price_asc":
            return sorted(rows, key=px1)
        if mode == "price_desc":
            return sorted(rows, key=lambda r: (r.get("median_x1") or 0), reverse=True)
        # recent (défaut) : par date de mise à jour décroissante
        return sorted(rows, key=lambda r: r.get("last_update") or "", reverse=True)

    # ── Pagination (scroll infini) ───────────────────────────────────
    def _load_more(self):
        start = self._shown
        end = min(start + PAGE_SIZE, len(self._filtered))
        for i in range(start, end):
            row_widget = self._make_row(self._filtered[i])
            # insérer avant le stretch final
            self._list_lay.insertWidget(self._list_lay.count() - 1, row_widget)
        self._shown = end

    def _on_scroll(self, value):
        sb = self._scroll.verticalScrollBar()
        # à 80% du bas → charger la page suivante
        if sb.maximum() > 0 and value >= sb.maximum() * 0.8:
            if self._shown < len(self._filtered):
                self._load_more()

    def _clear_list(self):
        # retirer toutes les lignes sauf le stretch et le status
        while self._list_lay.count() > 2:
            item = self._list_lay.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

    # ── Construction d'une ligne de prix ─────────────────────────────
    def _make_row(self, row):
        card = _card()
        col = QVBoxLayout(card)
        col.setContentsMargins(14, 10, 14, 10)
        col.setSpacing(6)

        # Ligne 1 : nom de la ressource + étoile favori
        row1 = QHBoxLayout()
        row1.setSpacing(6)
        name = _lbl(row.get("item_name", "?"), T.TEXT, "11pt", bold=True)
        name.setWordWrap(True)
        row1.addWidget(name, 1)

        item_id = row.get("item_id")
        is_fav = (item_id is not None and int(item_id) in self._favorites)
        star = QPushButton("★" if is_fav else "☆")
        star.setFixedSize(32, 32)
        star.setCursor(Qt.CursorShape.PointingHandCursor)
        star.setToolTip("Retirer des favoris" if is_fav else "Ajouter aux favoris")
        star.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;font-size:14pt;"
            f"padding:0;color:{T.GOLD if is_fav else T.HINT};}}"
            f"QPushButton:hover{{color:{T.GOLD};}}")
        star.clicked.connect(lambda _=False, r=row, b=star: self._toggle_favorite(r, b))
        row1.addWidget(star, alignment=Qt.AlignmentFlag.AlignTop)
        col.addLayout(row1)

        # Ligne 2 : lots de prix (l'un sous l'autre) + bouton signaler (droite)
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        lots_col = QVBoxLayout()
        lots_col.setSpacing(2)
        lots = [
            ("×1",   row.get("median_x1")),
            ("×10",  row.get("median_x10")),
            ("×100", row.get("median_x100")),
        ]
        any_lot = False
        for label, val in lots:
            if val is None:
                continue
            any_lot = True
            line = QHBoxLayout()
            line.setSpacing(6)
            lbl_lot = _lbl(label, T.HINT, "8pt")
            lbl_lot.setFixedWidth(34)
            line.addWidget(lbl_lot)
            line.addWidget(_lbl(f"{_fmt(val)} k", T.GREEN, "12pt", bold=True))
            line.addStretch()
            lots_col.addLayout(line)
        if not any_lot:
            lots_col.addWidget(_lbl("—", T.HINT, "12pt"))
        row2.addLayout(lots_col, 1)

        report = QPushButton("⚑  Signaler")
        report.setFixedHeight(30)
        report.setCursor(Qt.CursorShape.PointingHandCursor)
        report.setToolTip("Signaler un prix suspect")
        report.setStyleSheet(
            f"QPushButton{{background:transparent;color:{T.GOLD};"
            f"border:1px solid {T.GOLD};border-radius:6px;font-size:8pt;"
            f"font-weight:bold;padding:0 12px;}}"
            f"QPushButton:hover{{background:{T.GOLD};color:white;}}")
        sub_id = row.get("last_submission_id")
        report.clicked.connect(lambda _=False, sid=sub_id, nm=row.get("item_name"):
                               self._report(sid, nm))
        row2.addWidget(report, alignment=Qt.AlignmentFlag.AlignTop)
        col.addLayout(row2)

        # Ligne 3 : bouton Modifier (gauche) + "par pseudo" (droite)
        row3 = QHBoxLayout()
        row3.setSpacing(8)

        edit = QPushButton("✎  Modifier le prix")
        edit.setFixedHeight(30)
        edit.setCursor(Qt.CursorShape.PointingHandCursor)
        edit.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};border:none;"
            f"border-radius:6px;font-size:8pt;font-weight:bold;padding:0 12px;}}"
            f"QPushButton:hover{{background:{T.GRAD1};color:white;}}")
        edit.clicked.connect(lambda _=False, r=row: self._edit_price(r))
        row3.addWidget(edit)

        chart = QPushButton("📈")
        chart.setFixedSize(32, 32)
        chart.setCursor(Qt.CursorShape.PointingHandCursor)
        chart.setToolTip("Voir l'historique des prix")
        chart.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};border:none;"
            f"border-radius:6px;font-size:10pt;padding:0;margin:0;}}"
            f"QPushButton:hover{{background:{T.BLUE};color:white;}}")
        chart.clicked.connect(lambda _=False, r=row: self._show_history(r))
        row3.addWidget(chart)

        row3.addStretch()

        pseudo = row.get("last_pseudo", "—")
        ago = _time_ago(row.get("last_update"))
        meta = _lbl(f"par {pseudo} · {ago}", T.HINT, "8pt")
        meta.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row3.addWidget(meta)

        col.addLayout(row3)

        return card

    # ── Changement de serveur ────────────────────────────────────────
    def _on_server_change(self):
        self._server = self._server_cb.currentData()
        self._all_rows = []
        self._clear_list()
        self._load_prices()

    # ── Signalement ──────────────────────────────────────────────────
    def _report(self, sub_id, name):
        if sub_id is None:
            return
        dlg = _ConfirmDialog(
            "Signaler ce prix",
            f"Signaler le prix de « {name} » comme suspect ?\n\n"
            f"Si plusieurs joueurs le signalent, il sera masqué.",
            self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        res = api.report_price(sub_id)
        if res.get("ok"):
            if res.get("hidden"):
                self._toast("Prix masqué suite aux signalements.")
                self._load_prices()
            else:
                self._toast("Signalement envoyé. Merci !")
        else:
            self._toast("Signalement enregistré.")

    # ── Historique / graphique des prix ──────────────────────────────
    def _show_history(self, row):
        dlg = _HistoryDialog(self._server, row, self)
        dlg.exec()

    # ── Modifier le prix d'un item existant ──────────────────────────
    def _edit_price(self, row):
        # S'assurer que le pseudo est enregistré
        if not self._pseudo_registered():
            pd = _PseudoDialog(self._server, self)
            if pd.exec() != QDialog.DialogCode.Accepted:
                return
            pseudo = pd.pseudo()
            if len(pseudo) < 2:
                _info(self, "Pseudo", "Pseudo trop court (min. 2 caractères).")
                return
            reg = api.register(pseudo, self._server)
            if not reg.get("ok"):
                _info(self, "Erreur", api.error_message(reg))
                return
            self._mark_pseudo_registered()

        item = {"id": row.get("item_id"), "name": row.get("item_name")}
        dlg = _SubmitDialog(
            self._server, self._items_cache, self,
            locked_item=item,
            initial={
                "x1":   row.get("median_x1"),
                "x10":  row.get("median_x10"),
                "x100": row.get("median_x100"),
            })
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        item_id, px1, px10, px100 = dlg.result_data()
        if not px1:
            _info(self, "Prix", "Le prix du lot ×1 est obligatoire (ex : 1500).")
            return
        res = api.submit_price(self._server, item_id, px1, px10, px100)
        if res.get("ok"):
            self._toast("Prix mis à jour ! Merci 🙏")
            self._load_prices()
        else:
            _info(self, "Refusé", api.error_message(res), accent=T.RED)

    # ── Favoris ──────────────────────────────────────────────────────
    def _load_favorites(self) -> set:
        try:
            import model
            raw = model.load_config().get("hdv_favorites", [])
            return set(int(x) for x in raw)
        except Exception:
            return set()

    def _save_favorites(self):
        try:
            import model
            model.save_config({"hdv_favorites": list(self._favorites)})
        except Exception:
            pass

    def _toggle_favorite(self, row, btn=None):
        item_id = row.get("item_id")
        if item_id is None:
            return
        item_id = int(item_id)
        if item_id in self._favorites:
            self._favorites.discard(item_id)
        else:
            self._favorites.add(item_id)
        self._save_favorites()
        # Mettre à jour l'étoile cliquée sans tout recharger
        if btn is not None:
            fav = item_id in self._favorites
            btn.setText("★" if fav else "☆")
            btn.setStyleSheet(
                f"QPushButton{{background:transparent;border:none;font-size:14pt;"
                f"padding:0;color:{T.GOLD if fav else T.HINT};}}"
                f"QPushButton:hover{{color:{T.GOLD};}}")
            btn.setToolTip("Retirer des favoris" if fav else "Ajouter aux favoris")

    def _toggle_fav_panel(self):
        # Ouvrir/fermer le panneau inline
        if self._fav_panel.isVisible():
            self._fav_panel.setVisible(False)
            self._fav_btn.setText("⭐  Mes favoris")
            self._fit_window()
            return
        self._fill_fav_panel()
        self._fav_panel.setVisible(True)
        self._fav_btn.setText("⭐  Masquer les favoris")
        self._fit_window()

    def _fill_fav_panel(self):
        # Vider le panneau
        while self._fav_panel_lay.count():
            it = self._fav_panel_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        fav_rows = [r for r in self._all_rows if r.get("item_id") is not None and int(r.get("item_id")) in self._favorites]
        if not fav_rows:
            # panneau sans bordure quand vide
            self._fav_panel.setStyleSheet("QFrame{background:transparent;border:none;}")
            empty = _lbl("Aucun favori. Clique sur l'étoile ☆ d'un item pour l'ajouter.",
                         T.HINT, "8pt")
            empty.setStyleSheet(
                f"background:transparent;border:none;color:{T.HINT};font-size:8pt;")
            empty.setWordWrap(True)
            self._fav_panel_lay.addWidget(empty)
            return
        # panneau avec bordure quand il y a du contenu
        self._fav_panel.setStyleSheet(
            f"QFrame{{background:{T.BG_DARK};border:1px solid {T.BORDER};"
            f"border-radius:8px;}}")

        for r in fav_rows:
            line = QFrame()
            line.setStyleSheet(
                f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};"
                f"border-radius:6px;}}QLabel{{background:transparent;border:none;}}")
            ll = QHBoxLayout(line)
            ll.setContentsMargins(10, 6, 8, 6)
            ll.setSpacing(8)

            left = QVBoxLayout()
            left.setSpacing(2)
            left.addWidget(_lbl(r.get("item_name", "?"), T.TEXT, "9pt", bold=True))
            # Afficher les lots renseignés côte à côte
            lots_row = QHBoxLayout()
            lots_row.setSpacing(12)
            any_lot = False
            for label, key in [("×1", "median_x1"), ("×10", "median_x10"),
                               ("×100", "median_x100")]:
                v = r.get(key)
                if v is None:
                    continue
                any_lot = True
                box = QVBoxLayout()
                box.setSpacing(0)
                box.addWidget(_lbl(label, T.HINT, "7pt"))
                box.addWidget(_lbl(f"{_fmt(v)} k", T.GREEN, "9pt", bold=True))
                lots_row.addLayout(box)
            if not any_lot:
                lots_row.addWidget(_lbl("Pas de prix", T.HINT, "8pt"))
            lots_row.addStretch()
            left.addLayout(lots_row)
            ll.addLayout(left, 1)

            rm = QPushButton("🗑")
            rm.setFixedSize(32, 32)
            rm.setCursor(Qt.CursorShape.PointingHandCursor)
            rm.setToolTip("Retirer des favoris")
            rm.setStyleSheet(
                f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};border:none;"
                f"border-radius:6px;font-size:11pt;padding:0;}}"
                f"QPushButton:hover{{background:{T.RED};color:white;}}")
            rm.clicked.connect(lambda _=False, iid=r.get("item_id"): self._remove_favorite(iid))
            ll.addWidget(rm)

            self._fav_panel_lay.addWidget(line)

    def _remove_favorite(self, item_id):
        self._favorites.discard(int(item_id))
        self._save_favorites()
        self._fill_fav_panel()      # rafraîchir le panneau
        self._apply_filter()        # rafraîchir les étoiles de la liste
        self._fit_window()

    def _fit_window(self):
        from PySide6.QtCore import QTimer
        def do():
            w = self
            while w:
                w.updateGeometry()
                w = w.parentWidget()
            root = self.window()
            if root:
                root.setMinimumHeight(0)
                root.setMaximumHeight(16777215)
                root.adjustSize()
        QTimer.singleShot(0, do)

    # ── Soumission d'un prix ─────────────────────────────────────────
    def _open_submit(self):
        # Recharger le cache d'items s'il est vide (autocomplete)
        if not self._items_cache:
            res = api.search_items("", limit=3000)
            if isinstance(res, list):
                self._items_cache = res
        # 1) s'assurer que le pseudo est enregistré côté serveur
        if not self._pseudo_registered():
            dlg = _PseudoDialog(self._server, self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            pseudo = dlg.pseudo()
            if len(pseudo) < 2:
                _info(self, "Pseudo", "Pseudo trop court (min. 2 caractères).")
                return
            res = api.register(pseudo, self._server)
            if not res.get("ok"):
                _info(self, "Erreur", api.error_message(res))
                return
            self._mark_pseudo_registered()

        # 2) ouvrir le formulaire de prix
        dlg = _SubmitDialog(self._server, self._items_cache, self)
        result = dlg.exec()
        if result != QDialog.DialogCode.Accepted:
            return
        item_id, px1, px10, px100 = dlg.result_data()
        if not item_id:
            _info(self, "Item",
                "Item introuvable. Choisis un item proposé dans la liste "
                "déroulante en tapant son nom.")
            return
        if not px1:
            _info(self, "Prix", "Le prix du lot ×1 est obligatoire (ex : 1500).")
            return
        # Envoi synchrone
        res = api.submit_price(self._server, item_id, px1, px10, px100)
        if res.get("ok"):
            self._toast("Prix proposé ! Merci 🙏")
            self._load_prices()
        else:
            err = res.get("error", "")
            if err == "install_unknown":
                reg = api.register("Joueur", self._server)
                if reg.get("ok"):
                    self._mark_pseudo_registered()
                    res2 = api.submit_price(self._server, item_id, px1, px10, px100)
                    if res2.get("ok"):
                        self._toast("Prix proposé ! Merci 🙏")
                        self._load_prices()
                        return
                    res = res2
            _info(self, "Refusé", api.error_message(res), accent=T.RED)

    def _change_pseudo(self):
        # Récupérer le pseudo actuel depuis le serveur
        current = None
        info_txt = None
        try:
            me = api.get_my_pseudo()
            if me.get("ok"):
                current = me.get("pseudo")
                if not me.get("can_change"):
                    d = int(me.get("days_left", 0))
                    info_txt = (f"Tu pourras changer ton pseudo dans {d} jour"
                                f"{'s' if d > 1 else ''}.")
        except Exception:
            pass

        dlg = _PseudoDialog(self._server, self,
                            current_pseudo=current, info_text=info_txt)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        new_p = dlg.pseudo()
        if len(new_p) < 2:
            _info(self, "Pseudo", "Pseudo trop court (min. 2 caractères).")
            return
        res = api.register(new_p, self._server)
        if res.get("ok"):
            if res.get("changed"):
                self._mark_pseudo_registered()
                _info(self, "Pseudo",
                    f"Ton pseudo est maintenant « {res.get('pseudo')} ».")
            else:
                _info(self, "Pseudo", "C'est déjà ton pseudo actuel.")
        else:
            _info(self, "Impossible", api.error_message(res), accent=T.RED)

    def _pseudo_registered(self):
        import json
        from pathlib import Path
        f = Path.home() / ".retro_toolbox" / "hdv.json"
        if f.exists():
            try:
                return json.loads(f.read_text()).get("registered", False)
            except Exception:
                return False
        return False

    def _mark_pseudo_registered(self):
        import json
        from pathlib import Path
        base = Path.home() / ".retro_toolbox"
        base.mkdir(exist_ok=True)
        (base / "hdv.json").write_text(json.dumps({"registered": True}))

        _run_async(self, api.submit_price, on_done, self._server, item_id, price)

    # ── Petit toast (message éphémère) ───────────────────────────────
    def _toast(self, text):
        self._status.setText(text)
        self._status.setVisible(True)
        def restore():
            if len(self._filtered) == 0 and len(self._all_rows) == 0:
                self._status.setText("Aucun prix pour le moment.\nSois le premier à en proposer un ! 💰")
                self._status.setVisible(True)
            else:
                self._status.setVisible(False)
        QTimer.singleShot(2500, restore)


# ─── Dialogue de soumission de prix ───────────────────────────────────
class _SubmitDialog(QDialog):
    def __init__(self, server, items, parent=None, locked_item=None, initial=None):
        super().__init__(parent)
        is_edit = locked_item is not None
        self.setWindowTitle("Modifier le prix" if is_edit else "Proposer un prix")
        self.setFixedWidth(340)
        self.setStyleSheet(f"QDialog{{background:{T.BG};}}")
        self._items = list(items)
        self._item_id = locked_item["id"] if is_edit else None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)

        lay.addWidget(_lbl(f"Serveur : {server.capitalize()}", T.SUBTEXT, "9pt", bold=True))

        # Champ item (verrouillé en mode édition)
        lay.addWidget(_lbl("Item", T.HINT, "8pt"))
        self._item_inp = QLineEdit()
        self._item_inp.setPlaceholderText("Commence à taper le nom…")
        self._item_inp.setFixedHeight(34)
        self._item_inp.setStyleSheet(
            f"QLineEdit{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:8px;padding:2px 10px;color:{T.TEXT};font-size:10pt;}}"
            f"QLineEdit:focus{{border:1px solid {T.ORANGE};}}")
        self._names = [it["name"] for it in self._items]

        if is_edit:
            # item figé : on affiche le nom, champ non éditable
            self._item_inp.setText(locked_item["name"])
            self._item_inp.setReadOnly(True)
            self._item_inp.setStyleSheet(
                f"QLineEdit{{background:{T.BG_DARK};border:1px solid {T.BORDER};"
                f"border-radius:8px;padding:2px 10px;color:{T.SUBTEXT};"
                f"font-size:10pt;font-weight:bold;}}")
        else:
            self._model = QStringListModel(self._names)
            self._completer = QCompleter(self._model)
            self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
            self._completer.setMaxVisibleItems(12)
            self._completer.popup().setStyleSheet(
                f"QListView{{background:{T.SURFACE};color:{T.TEXT};"
                f"border:1px solid {T.BORDER};border-radius:8px;outline:none;"
                f"font-size:10pt;padding:4px;}}"
                f"QListView::item{{padding:6px 8px;border-radius:6px;}}"
                f"QListView::item:selected{{background:{T.BG_DARK};color:{T.ORANGE};}}"
                f"QListView::item:hover{{background:{T.BG_DARK};}}")
            self._item_inp.setCompleter(self._completer)
            self._item_inp.textEdited.connect(self._on_item_typed)
        lay.addWidget(self._item_inp)

        # Champs prix par lot
        lay.addWidget(_lbl("Prix en kamas", T.HINT, "8pt"))

        def _price_field(placeholder):
            e = QLineEdit()
            e.setPlaceholderText(placeholder)
            e.setFixedHeight(34)
            e.setStyleSheet(
                f"QLineEdit{{background:{T.SURFACE};border:1px solid {T.BORDER};"
                f"border-radius:8px;padding:2px 10px;color:{T.TEXT};font-size:10pt;}}"
                f"QLineEdit:focus{{border:1px solid {T.ORANGE};}}")
            return e

        # ×1 (obligatoire)
        r1 = QHBoxLayout(); r1.setSpacing(8)
        lbl1 = _lbl("Lot ×1", T.TEXT, "9pt", bold=True)
        lbl1.setFixedWidth(54)
        r1.addWidget(lbl1)
        self._px1 = _price_field("Obligatoire — ex : 1500")
        r1.addWidget(self._px1)
        lay.addLayout(r1)

        # ×10 (optionnel)
        r10 = QHBoxLayout(); r10.setSpacing(8)
        lbl10 = _lbl("Lot ×10", T.SUBTEXT, "9pt")
        lbl10.setFixedWidth(54)
        r10.addWidget(lbl10)
        self._px10 = _price_field("Optionnel")
        r10.addWidget(self._px10)
        lay.addLayout(r10)

        # ×100 (optionnel)
        r100 = QHBoxLayout(); r100.setSpacing(8)
        lbl100 = _lbl("Lot ×100", T.SUBTEXT, "9pt")
        lbl100.setFixedWidth(54)
        r100.addWidget(lbl100)
        self._px100 = _price_field("Optionnel")
        r100.addWidget(self._px100)
        lay.addLayout(r100)

        # Formatage automatique avec espaces de milliers pendant la frappe
        for field in (self._px1, self._px10, self._px100):
            field.textChanged.connect(
                lambda _=None, f=field: self._format_price_field(f))

        # Pré-remplir en mode édition (avec formatage)
        if initial:
            if initial.get("x1") is not None:
                self._px1.setText(_fmt(int(initial["x1"])))
            if initial.get("x10") is not None:
                self._px10.setText(_fmt(int(initial["x10"])))
            if initial.get("x100") is not None:
                self._px100.setText(_fmt(int(initial["x100"])))

        # Boutons
        row = QHBoxLayout()
        cancel = QPushButton("Annuler")
        cancel.setFixedHeight(34)
        cancel.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};border:none;"
            f"border-radius:8px;font-size:9pt;}}")
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)

        ok = QPushButton("Envoyer")
        ok.setFixedHeight(34)
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
            f"border-radius:8px;font-size:9pt;font-weight:bold;}}")
        ok.clicked.connect(self.accept)
        row.addWidget(ok)
        lay.addLayout(row)

    def _on_item_typed(self, text):
        # Si peu de résultats locaux, compléter depuis le serveur
        text = text.strip()
        if len(text) < 2:
            return
        import hdv_prices as api
        found = [n for n in self._names if text.lower() in n.lower()]
        if len(found) < 3:
            res = api.search_items(text, limit=30)
            if isinstance(res, list):
                for it in res:
                    if it["name"] not in self._names:
                        self._names.append(it["name"])
                        self._items.append(it)
                self._model.setStringList(self._names)

    def _format_price_field(self, field):
        """Reformate le champ avec des espaces de milliers, curseur préservé."""
        if getattr(self, "_formatting", False):
            return
        self._formatting = True
        try:
            text = field.text()
            # Position du curseur et nb de chiffres avant le curseur
            cursor = field.cursorPosition()
            digits_before = sum(1 for c in text[:cursor] if c.isdigit())
            # Extraire uniquement les chiffres
            digits = "".join(c for c in text if c.isdigit())
            if not digits:
                field.setText("")
                self._formatting = False
                return
            # Formater avec espaces
            formatted = f"{int(digits):,}".replace(",", " ")
            field.setText(formatted)
            # Repositionner le curseur après le bon nombre de chiffres
            new_pos = 0
            seen = 0
            for i, c in enumerate(formatted):
                if seen >= digits_before:
                    break
                if c.isdigit():
                    seen += 1
                new_pos = i + 1
            field.setCursorPosition(new_pos)
        finally:
            self._formatting = False

    def result_data(self):
        name = self._item_inp.text().strip()
        # 1. chercher dans le cache local (sauf si item déjà figé en mode édition)
        if self._item_id is None:
            for it in self._items:
                if it["name"].lower() == name.lower():
                    self._item_id = it["id"]
                    break
        # 2. fallback : chercher directement sur le serveur (nom exact)
        if self._item_id is None and name:
            import hdv_prices as api
            res = api.search_items(name, limit=20)
            if isinstance(res, list):
                for it in res:
                    if it["name"].lower() == name.lower():
                        self._item_id = it["id"]
                        break
                # si aucun match exact, prendre le 1er résultat proche
                if self._item_id is None and res:
                    self._item_id = res[0]["id"]
        def _parse(field):
            t = field.text().replace(" ", "").replace(".", "").replace(",", "").strip()
            if not t:
                return None
            try:
                v = int(t)
                return v if v > 0 else None
            except ValueError:
                return None

        px1   = _parse(self._px1)
        px10  = _parse(self._px10)
        px100 = _parse(self._px100)
        return self._item_id, px1, px10, px100


# ─── Graphique en courbe (dessin QPainter, sans dépendance externe) ───
class _LineChart(QWidget):
    """Trace une courbe de prix avec axes, grille et dégradé sous la courbe."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._points = []   # liste de (date_str, valeur|None)
        self.setMinimumHeight(220)

    def set_data(self, points):
        self._points = points or []
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        ml, mr, mt, mb = 56, 14, 14, 28   # marges (gauche pour les prix, bas pour dates)
        cw = w - ml - mr
        ch = h - mt - mb

        # Fond
        p.fillRect(self.rect(), QColor(T.SURFACE))

        vals = [(i, v) for i, (_, v) in enumerate(self._points) if v is not None]
        if len(vals) < 1:
            p.setPen(QColor(T.HINT))
            f = QFont(); f.setPointSize(10); p.setFont(f)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "Pas assez de données pour cette période")
            p.end()
            return

        vmin = min(v for _, v in vals)
        vmax = max(v for _, v in vals)
        if vmin == vmax:
            vmin = vmin * 0.9
            vmax = vmax * 1.1 if vmax > 0 else 1
        span = max(1, vmax - vmin)
        n = len(self._points)

        def x_at(i):
            if n <= 1:
                return ml + cw / 2
            return ml + cw * i / (n - 1)

        def y_at(v):
            return mt + ch * (1 - (v - vmin) / span)

        # Grille horizontale + labels de prix (4 niveaux)
        p.setFont(QFont("", 7))
        for k in range(5):
            gy = mt + ch * k / 4
            p.setPen(QPen(QColor(T.BORDER), 1, Qt.PenStyle.DashLine))
            p.drawLine(int(ml), int(gy), int(ml + cw), int(gy))
            val = vmax - span * k / 4
            p.setPen(QColor(T.HINT))
            label = f"{int(val):,}".replace(",", " ") + " k"
            p.drawText(QRectF(0, gy - 8, ml - 6, 16),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)

        # Construire le chemin de la courbe (uniquement points non-null)
        path = QPainterPath()
        fill = QPainterPath()
        started = False
        for i, v in vals:
            x = x_at(i); y = y_at(v)
            if not started:
                path.moveTo(x, y)
                fill.moveTo(x, mt + ch)
                fill.lineTo(x, y)
                started = True
            else:
                path.lineTo(x, y)
                fill.lineTo(x, y)
        # Fermer le remplissage
        last_x = x_at(vals[-1][0])
        fill.lineTo(last_x, mt + ch)
        fill.closeSubpath()

        # Dégradé sous la courbe
        grad = QLinearGradient(0, mt, 0, mt + ch)
        c1 = QColor(T.GRAD1); c1.setAlpha(90)
        c2 = QColor(T.GRAD1); c2.setAlpha(10)
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        p.fillPath(fill, QBrush(grad))

        # Courbe
        p.setPen(QPen(QColor(T.GRAD1), 2.5))
        p.drawPath(path)

        # Points
        p.setBrush(QBrush(QColor(T.GRAD2)))
        p.setPen(QPen(QColor("white"), 1.5))
        for i, v in vals:
            p.drawEllipse(QPointF(x_at(i), y_at(v)), 3.5, 3.5)

        # Labels de dates (premier, milieu, dernier)
        p.setPen(QColor(T.HINT))
        p.setFont(QFont("", 7))
        idxs = sorted(set([0, n // 2, n - 1]))
        for i in idxs:
            if 0 <= i < n:
                d = self._points[i][0]
                # format court JJ/MM
                short = d[8:10] + "/" + d[5:7] if len(d) >= 10 else d
                p.drawText(QRectF(x_at(i) - 24, mt + ch + 4, 48, 16),
                           Qt.AlignmentFlag.AlignCenter, short)
        p.end()


class _HistoryDialog(QDialog):
    """Dialogue : graphique d'historique des prix avec sélecteurs période/lot."""

    def __init__(self, server, row, parent=None):
        super().__init__(parent)
        self._server = server
        self._item_id = row.get("item_id")
        self._item_name = row.get("item_name", "?")
        self._days = 30
        self._lot = "x1"
        self._cache = {}   # {days: data}

        self.setWindowTitle(f"Historique — {self._item_name}")
        self.setFixedSize(480, 380)
        self.setStyleSheet(f"QDialog{{background:{T.BG};}}")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(12)

        # Titre
        lay.addWidget(_lbl(f"📈  {self._item_name}", T.TEXT, "13pt", bold=True))
        lay.addWidget(_lbl(f"Serveur : {server.capitalize()}", T.HINT, "8pt"))

        # Sélecteurs
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        # Période
        self._period_cb = QComboBox()
        for d, lab in [(7, "7 jours"), (15, "15 jours"), (30, "30 jours")]:
            self._period_cb.addItem(lab, d)
        self._period_cb.setCurrentIndex(2)
        self._period_cb.setFixedHeight(30)
        self._period_cb.setStyleSheet(self._combo_style())
        self._period_cb.currentIndexChanged.connect(self._on_period)
        ctrl.addWidget(self._period_cb, 1)

        # Lot
        self._lot_cb = QComboBox()
        for v, lab in [("x1", "Lot ×1"), ("x10", "Lot ×10"), ("x100", "Lot ×100")]:
            self._lot_cb.addItem(lab, v)
        self._lot_cb.setFixedHeight(30)
        self._lot_cb.setStyleSheet(self._combo_style())
        self._lot_cb.currentIndexChanged.connect(self._on_lot)
        ctrl.addWidget(self._lot_cb, 1)
        lay.addLayout(ctrl)

        # Graphique
        self._chart = _LineChart()
        chart_frame = QFrame()
        chart_frame.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:10px;}}")
        cf = QVBoxLayout(chart_frame)
        cf.setContentsMargins(6, 6, 6, 6)
        cf.addWidget(self._chart)
        lay.addWidget(chart_frame, 1)

        # Bouton fermer
        close = QPushButton("Fermer")
        close.setFixedHeight(32)
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};border:none;"
            f"border-radius:8px;font-size:9pt;font-weight:bold;}}"
            f"QPushButton:hover{{color:{T.TEXT}}};")
        close.clicked.connect(self.accept)
        lay.addWidget(close)

        self._load()

    def _combo_style(self):
        return (
            f"QComboBox{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:8px;padding:2px 10px;color:{T.TEXT};font-size:9pt;}}"
            f"QComboBox::drop-down{{border:none;width:20px;}}"
            f"QComboBox QAbstractItemView{{background:{T.SURFACE};color:{T.TEXT};"
            f"selection-background-color:{T.BG_DARK};border:1px solid {T.BORDER};}}")

    def _on_period(self):
        self._days = self._period_cb.currentData()
        self._load()

    def _on_lot(self):
        self._lot = self._lot_cb.currentData()
        self._render()

    def _load(self):
        if self._days in self._cache:
            self._render()
            return
        data = api.price_history(self._server, self._item_id, self._days)
        self._cache[self._days] = data if isinstance(data, list) else []
        self._render()

    def _render(self):
        data = self._cache.get(self._days, [])
        points = [(d.get("jour", ""), d.get(self._lot)) for d in data]
        self._chart.set_data(points)
