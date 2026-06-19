"""characters_panel.py — Liste ordonnée des fenêtres Dofus avec drag & drop."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QPoint, QEvent, QObject, Signal
import theme as T
from tabs.accounts.window_manager import (
    collect_sessions, activate_window, is_game_focused,
    foreground_handle, SessionEntry
)


def _lbl(txt, color=None, sz="9pt", bold=False, italic=False):
    l = QLabel(txt)
    ss = f"background:transparent;font-size:{sz};"
    if color:  ss += f"color:{color};"
    if bold:   ss += "font-weight:bold;"
    if italic: ss += "font-style:italic;"
    l.setStyleSheet(ss)
    return l


def _ibtn(text, bg, fg, hov, h=22):
    b = QPushButton(text)
    b.setFixedHeight(h)
    b.setStyleSheet(
        f"QPushButton{{background:{bg};color:{fg};border:none;"
        f"padding:2px 8px;font-size:9pt;font-weight:bold;}}"
        f"QPushButton:hover{{background:{hov};}}")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


# ── Icônes SVG pour le mode compact ────────────────────────────────────────
_SVG_STAR_ON = (
    '<svg viewBox="0 0 24 24" fill="#e07a1f" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25'
    'L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>'
)
_SVG_STAR_OFF = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="#aaa" stroke-width="1.8"'
    ' xmlns="http://www.w3.org/2000/svg">'
    '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25'
    'L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>'
)
_SVG_CROSS = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="#e05555" stroke-width="2.2"'
    ' stroke-linecap="round" xmlns="http://www.w3.org/2000/svg">'
    '<line x1="5" y1="5" x2="19" y2="19"/>'
    '<line x1="19" y1="5" x2="5" y2="19"/></svg>'
)
_SVG_EXCLUDE = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="#aaa" stroke-width="1.8"'
    ' stroke-linecap="round" xmlns="http://www.w3.org/2000/svg">'
    '<circle cx="12" cy="12" r="9"/>'
    '<line x1="8" y1="12" x2="16" y2="12"/></svg>'
)


def _svg_btn(svg: str, bg: str, tooltip: str) -> QPushButton:
    """Bouton carré avec icône SVG rendue via QPixmap."""
    from PySide6.QtGui import QPixmap, QIcon
    from PySide6.QtCore import QByteArray
    b = QPushButton()
    b.setFixedSize(28, 28)
    b.setToolTip(tooltip)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(
        f"QPushButton{{background:{bg};border:none;border-radius:6px;padding:0;}}"
        f"QPushButton:hover{{background:rgba(255,255,255,30);}}")
    px = QPixmap()
    px.loadFromData(QByteArray(svg.encode()), "SVG")
    px = px.scaled(18, 18,
                   Qt.AspectRatioMode.KeepAspectRatio,
                   Qt.TransformationMode.SmoothTransformation)
    b.setIcon(QIcon(px))
    b.setIconSize(px.size())
    return b


class _SlotRow(QFrame):
    """Ligne représentant un personnage dans la liste."""

    def __init__(self, idx: int, win: SessionEntry,
                 is_main: bool, is_skip: bool, is_active: bool,
                 panel: "AccountPanel"):
        super().__init__()
        self._idx = idx
        self._win = win
        self._panel = panel

        hl = (panel._drag_idx == idx)
        if hl:
            bg = '#2a1e0e'
        elif is_active:
            bg = '#1a2a1a'   # vert très sombre pour le tour actif
        else:
            bg = T.SURFACE

        border_l = f"border-left:3px solid {T.ORANGE};" if (is_active and not hl) else ""
        border_drag = f"border-left:3px solid {T.GOLD};" if hl else ""
        self.setStyleSheet(
            f"QFrame{{background:{bg};{border_l}{border_drag}"
            f"border-bottom:1px solid {T.BORDER};}}"
            f"QFrame:hover{{background:{T.SURFACE2};}}"
            f"QFrame QLabel{{border:none;background:transparent;}}"
            f"QFrame QPushButton{{border:none;}}")

        compact = getattr(panel, "_compact", False)

        if compact:
            # Mode compact : tout sur une ligne, marges réduites
            outer = QHBoxLayout(self)
            outer.setContentsMargins(4, 2, 4, 2)
            outer.setSpacing(4)

            hdl = QLabel("⠿")
            hdl.setStyleSheet(f"color:{T.ORANGE if hl else T.HINT};background:transparent;font-size:11pt;")
            hdl.setCursor(Qt.CursorShape.SizeAllCursor)
            hdl.setFixedWidth(12)

            rang = _lbl(f"{idx + 1}.", T.HINT, "9pt")
            rang.setFixedWidth(16)

            if win.loading: name_color = T.HINT
            elif hl: name_color = T.ORANGE
            elif is_active and not hl: name_color = '#7ab87a'
            elif is_skip: name_color = T.RED
            else: name_color = T.TEXT
            lname = QLabel(win.pseudo)
            lname.setStyleSheet(
                f"color:{name_color};background:transparent;font-weight:bold;font-size:9pt;"
                f"font-style:{'italic' if win.loading else 'normal'};"
                + ("text-decoration:line-through;" if is_skip and not win.loading else ""))

            if is_active and not hl:
                arrow = QLabel("▶")
                arrow.setStyleSheet("color:#7ab87a;background:transparent;font-size:8pt;")
                outer.addWidget(arrow)
            outer.addWidget(hdl); outer.addWidget(rang); outer.addWidget(lname, 1)

            btn_m = _svg_btn(
                _SVG_STAR_ON if is_main else _SVG_STAR_OFF,
                "rgba(217,121,31,45)" if is_main else "transparent",
                "Retirer principal" if is_main else "Définir principal")
            btn_m.clicked.connect(lambda: panel._set_main(win.pseudo))
            outer.addWidget(btn_m)

            if not win.loading:
                btn_s = _svg_btn(
                    _SVG_CROSS if is_skip else _SVG_EXCLUDE,
                    "rgba(140,64,56,45)" if is_skip else "transparent",
                    "Réintégrer" if is_skip else "Exclure du cycle")
                btn_s.clicked.connect(lambda: panel._toggle_skip(win.pseudo))
                outer.addWidget(btn_s)

        else:
            # Mode normal : 2 lignes
            outer = QVBoxLayout(self)
            outer.setContentsMargins(8, 7, 8, 7)
            outer.setSpacing(5)

            r1 = QHBoxLayout(); r1.setSpacing(6)
            hdl = QLabel("⠿")
            hdl.setStyleSheet(f"color:{T.ORANGE if hl else T.HINT};background:transparent;font-size:13pt;")
            hdl.setCursor(Qt.CursorShape.SizeAllCursor)
            hdl.setFixedWidth(14)
            rang = _lbl(f"{idx + 1}.", T.HINT, "10pt")
            rang.setFixedWidth(20)

            if win.loading: name_color = T.HINT
            elif hl: name_color = T.ORANGE
            elif is_active and not hl: name_color = '#7ab87a'
            elif is_skip: name_color = T.RED
            else: name_color = T.TEXT
            lname = QLabel(win.pseudo)
            lname.setStyleSheet(
                f"color:{name_color};background:transparent;"
                f"font-weight:bold;font-size:10pt;font-style:{'italic' if win.loading else 'normal'};"
                + ("text-decoration:line-through;" if is_skip and not win.loading else ""))

            if is_active and not hl:
                arrow = QLabel("▶")
                arrow.setStyleSheet("color:#7ab87a;background:transparent;font-size:9pt;")
                r1.addWidget(arrow)
            r1.addWidget(hdl); r1.addWidget(rang); r1.addWidget(lname, 1)
            outer.addLayout(r1)

            r2 = QHBoxLayout(); r2.setSpacing(4)
            if is_main:
                b = QLabel("⭐ Principal")
                b.setStyleSheet(f"background:{T.ORANGE};color:white;font-size:8pt;font-weight:bold;padding:1px 5px;")
                r2.addWidget(b)
            elif is_skip:
                b = QLabel("🚫 Exclu du cycle")
                b.setStyleSheet(f"background:{T.RED};color:white;font-size:8pt;font-weight:bold;padding:1px 5px;")
                r2.addWidget(b)
            r2.addStretch()
            btn_m = _svg_btn(
                _SVG_STAR_ON if is_main else _SVG_STAR_OFF,
                "rgba(217,121,31,45)" if is_main else T.BG_DARK,
                "Retirer principal" if is_main else "Définir principal")
            btn_m.clicked.connect(lambda: panel._set_main(win.pseudo))
            r2.addWidget(btn_m)
            if not win.loading:
                btn_s = _svg_btn(
                    _SVG_CROSS if is_skip else _SVG_EXCLUDE,
                    "rgba(140,64,56,45)" if is_skip else T.BG_DARK,
                    "Réintégrer" if is_skip else "Exclure du cycle")
                btn_s.clicked.connect(lambda: panel._toggle_skip(win.pseudo))
                r2.addWidget(btn_s)
            outer.addLayout(r2)

        # ── Drag targets ───────────────────────────────────
        for w in [self, hdl, rang, lname]:
            w.mousePressEvent = lambda e, i=idx: panel._drag_start(i, e)


class AccountPanel(QWidget):
    """Panneau de gestion des personnages avec détection automatique."""

    char_switched = Signal(int)

    def __init__(self, cfg: dict, on_save, on_focus_changed=None, parent=None):
        super().__init__(parent)
        self._cfg       = cfg
        self._on_save   = on_save
        self._windows:  list[SessionEntry] = []
        self._main:     str | None = cfg.get("char_main")
        self._excluded:  set[str]   = set(cfg.get("char_skip", []))
        self._drag_idx: int | None = None
        self._row_tops: list[int]  = []
        self._row_h:    int        = 80
        self._prev_hwnd:  int | None = None
        self._active_pseudo: str | None = None
        self._build()
        self._start_poll()

    # ── Construction ───────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        self._hdr = QFrame()
        hdr = self._hdr
        hdr.setStyleSheet(
            f"background:{T.BG_DARK};")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(10, 6, 10, 6); hl.setSpacing(6)
        hl.addWidget(_lbl("Fenêtres Dofus", T.TEXT, "9pt", bold=True), 1)
        self._status = _lbl("", T.HINT, "9pt")
        hl.addWidget(self._status)
        btn_scan = QPushButton("🔄")
        btn_scan.setFixedSize(24, 24)
        btn_scan.setStyleSheet(
            f"QPushButton{{background:transparent;color:{T.HINT};border:none;font-size:10pt;}}"
            f"QPushButton:hover{{color:{T.ORANGE};}}")
        btn_scan.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_scan.clicked.connect(self._discover)
        hl.addWidget(btn_scan)
        root.addWidget(hdr)

        # Zone scrollable
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFixedHeight(490)
        self._scroll.setStyleSheet(
            f"QScrollArea{{background:{T.BG};border:none;}}"
            f"QScrollBar:vertical{{background:{T.BG_DARK};width:4px;}}"
            f"QScrollBar::handle:vertical{{background:{T.BORDER2};min-height:20px;}}"
            f"QScrollBar::handle:vertical:hover{{background:{T.ORANGE};}}"
            f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        self._container = QWidget()
        self._container.setStyleSheet(f"background:{T.BG};")
        self._clay = QVBoxLayout(self._container)
        self._clay.setContentsMargins(0, 0, 0, 0)
        self._clay.setSpacing(0)
        self._clay.addStretch()
        self._scroll.setWidget(self._container)
        root.addWidget(self._scroll)

        # Footer : hint
        self._ftr = QFrame()
        ftr = self._ftr
        ftr.setStyleSheet(f"background:{T.SURFACE};border:none;")
        fv = QVBoxLayout(ftr); fv.setContentsMargins(10,5,10,5); fv.setSpacing(4)
        fv.addWidget(_lbl(
            "⠿ Glisse pour réordonner  ·  ★ = principal  ·  ○ = exclure",
            T.HINT, "9pt", italic=True))
        root.addWidget(ftr)

        # ── Bouton barre des tâches — AU DESSUS de profils ───
        from PySide6.QtWidgets import QComboBox
        self._btn_save_order = QPushButton("🖥  Appliquer l'ordre dans la barre des tâches")
        btn_save = self._btn_save_order
        btn_save.setFixedHeight(34)
        btn_save.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
            f"padding:4px 10px;font-size:10pt;font-weight:700;"
            f"border-radius:8px;}}"
            f"QPushButton:hover{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});}}")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self._save_order)
        root.addWidget(btn_save)

        # ── Profils d'ordre ───────────────────────────────────
        self._prof_frame = QFrame()
        prof_frame = self._prof_frame
        prof_frame.setStyleSheet(f"background:{T.BG_DARK};border:none;")
        pl = QVBoxLayout(prof_frame); pl.setContentsMargins(8,8,8,8); pl.setSpacing(6)

        pl.addWidget(_lbl("📋 Profils d'ordre", T.TEXT, "10pt", bold=True))

        # ComboBox profils
        self._profile_combo = QComboBox()
        self._profile_combo.setFixedHeight(30)
        self._profile_combo.setStyleSheet(
            f"QComboBox{{background:{T.SURFACE};color:{T.TEXT};border:none;"
            f"padding:4px 8px;font-size:9pt;}}"
            f"QComboBox QAbstractItemView{{background:{T.SURFACE};color:{T.TEXT};"
            f"selection-background-color:{T.ORANGE};}}")
        self._profile_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        pl.addWidget(self._profile_combo)

        # Ligne : Appliquer + Supprimer
        row_ap = QHBoxLayout(); row_ap.setSpacing(5)
        btn_apply_prof = QPushButton("▶  Appliquer")
        btn_del_prof   = QPushButton("✕  Supprimer")
        for btn, bg, fg, hov, radius in [
            (btn_apply_prof, "grad", "white",  "grad", 8),
            (btn_del_prof,   T.BG_DARK, T.RED, T.RED, 8),
        ]:
            btn.setFixedHeight(30)
            if bg == "grad":
                btn.setStyleSheet(
                    f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                    f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
                    f"padding:4px 10px;font-size:9pt;font-weight:700;border-radius:{radius}px;}}")
            else:
                btn.setStyleSheet(
                    f"QPushButton{{background:{bg};color:{fg};border:1px solid {T.BORDER};"
                    f"padding:4px 10px;font-size:9pt;font-weight:700;border-radius:{radius}px;}}"
                    f"QPushButton:hover{{background:{hov};color:white;border:none;}}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            row_ap.addWidget(btn)
        pl.addLayout(row_ap)

        # Bouton Sauvegarder profil
        btn_save_prof = QPushButton("💾  Nommer et sauvegarder cet ordre")
        btn_save_prof.setFixedHeight(32)
        btn_save_prof.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
            f"padding:4px 10px;font-size:10pt;font-weight:700;"
            f"border-radius:8px;}}"
            f"QPushButton:hover{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});}}")
        btn_save_prof.setCursor(Qt.CursorShape.PointingHandCursor)
        pl.addWidget(btn_save_prof)

        root.addWidget(prof_frame)

        self._profiles: dict[str, list[str]] = dict(self._cfg.get("order_profiles", {}))
        self._refresh_profile_combo()

        btn_apply_prof.clicked.connect(self._apply_profile)
        btn_save_prof.clicked.connect(self._save_profile)
        btn_del_prof.clicked.connect(self._delete_profile)
        # Sauvegarder le profil sélectionné dès que la sélection change
        self._profile_combo.currentTextChanged.connect(self._on_profile_selected)

    # ── Scan & refresh ─────────────────────────────────────

    def _discover(self):
        fresh = collect_sessions()
        fresh_map = {w.hwnd: w for w in fresh}
        old_hwnds = {w.hwnd for w in self._windows}
        # Préserver l'ordre ET mettre à jour les données (titre, pseudo, loading…)
        kept = [fresh_map[w.hwnd] for w in self._windows if w.hwnd in fresh_map]
        seen = {w.hwnd for w in kept}
        for w in fresh:
            if w.hwnd not in seen:
                kept.append(w)
        # Maximiser les nouvelles fenêtres si option activée
        new_hwnds = {w.hwnd for w in kept} - old_hwnds
        if new_hwnds and self._cfg.get("settings", {}).get("maximize_on_launch", False):
            import sys as _msys
            if _msys.platform == "win32":
                try:
                    import win32gui, win32con
                    for hwnd in new_hwnds:
                        try: win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                        except: pass
                except: pass
        self._windows = kept
        n = len(self._windows)
        self._status.setText(f"{n} fenêtre{'s' if n != 1 else ''}")
        self._render()

    def _render(self, highlight: int | None = None):
        compact = getattr(self, "_compact", False)

        # En mode compact : vider tout (pas de stretch à garder)
        # En mode normal : garder le dernier item (le stretch)
        limit = 0 if compact else 1
        while self._clay.count() > limit:
            item = self._clay.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._row_tops = []

        if not self._windows:
            msg = _lbl("Aucune fenêtre Dofus détectée.\nOuvre le jeu puis clique 🔄",
                       T.HINT, "10pt", italic=True)
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg.setContentsMargins(0, 30, 0, 30)
            self._clay.insertWidget(0, msg)
            return

        for i, win in enumerate(self._windows):
            row = _SlotRow(i, win,
                           is_main=(win.pseudo == self._main),
                           is_skip=(win.pseudo in self._excluded and not win.loading),
                           is_active=(win.pseudo == self._active_pseudo),
                           panel=self)
            self._clay.insertWidget(i, row)

        if compact:
            n = max(1, len(self._windows))
            self._scroll.setFixedHeight(min(n * 30, 400))
            QTimer.singleShot(0, self._compute_heights)  # pour le drag
        else:
            QTimer.singleShot(0, self._compute_heights)

    def _compute_heights(self):
        self._row_tops = []
        for i in range(self._clay.count()):
            item = self._clay.itemAt(i)
            if item and item.widget() and item.widget().height() > 1:
                y = item.widget().mapTo(self._container, QPoint(0, 0)).y()
                self._row_tops.append(y)
                self._row_h = item.widget().height()

    # ── Drag & Drop ────────────────────────────────────────

    def _drag_start(self, idx: int, event):
        self._drag_idx = idx
        if not self._row_tops:
            self._compute_heights()
        self._render(highlight=idx)

        class _InputFilter(QObject):
            def __init__(self, p):
                super().__init__()
                self._p = p
            def eventFilter(self, obj, evt):
                t = evt.type()
                if t == QEvent.Type.MouseMove:
                    self._p._drag_move(evt)
                elif (t == QEvent.Type.MouseButtonRelease
                      and evt.button() == Qt.MouseButton.LeftButton):
                    self._p._drag_finish(evt)
                return False

        self._ev_filter = _InputFilter(self)
        QApplication.instance().installEventFilter(self._ev_filter)

    def _drag_move(self, event):
        if self._drag_idx is None or not self._row_tops:
            return
        try:
            gpos   = event.globalPosition().toPoint()
            local  = self._container.mapFromGlobal(gpos)
            inner_y = local.y() + self._scroll.verticalScrollBar().value()
        except Exception:
            return

        target = self._drag_idx
        for i, top in enumerate(self._row_tops):
            bot = (self._row_tops[i + 1]
                   if i + 1 < len(self._row_tops)
                   else top + self._row_h)
            if top <= inner_y < bot:
                target = i
                break

        if target != self._drag_idx:
            self._windows[self._drag_idx], self._windows[target] = \
                self._windows[target], self._windows[self._drag_idx]
            self._drag_idx = target
            self._render(highlight=target)

    def _drag_finish(self, event):
        if hasattr(self, "_ev_filter") and self._ev_filter:
            QApplication.instance().removeEventFilter(self._ev_filter)
            self._ev_filter = None
        self._drag_idx = None
        self._render()

    # ── Actions ────────────────────────────────────────────

    def _set_main(self, pseudo: str):
        self._main = None if self._main == pseudo else pseudo
        self._cfg["char_main"] = self._main or ""
        self._on_save()
        self._render()

    def _toggle_skip(self, pseudo: str):
        if pseudo in self._excluded:
            self._excluded.discard(pseudo)
        else:
            self._excluded.add(pseudo)
        self._cfg["char_skip"] = list(self._excluded)
        self._on_save()
        self._render()

    def _save_order(self):
        self._on_save()
        self._status.setText("⏳ Réordonnancement…")
        hwnds = [w.hwnd for w in self._windows if w.hwnd]
        if hwnds:
            import threading
            threading.Thread(target=self._do_reorder, args=(hwnds,), daemon=True).start()
        else:
            self._status.setText("✅ Sauvegardé")

    def _do_reorder(self, hwnds):
        import sys as _rsys
        if _rsys.platform == "darwin":
            # macOS : pas de barre des tâches, on remet juste les fenêtres
            # au premier plan dans l'ordre choisi (z-order)
            try:
                from os_bridge.bridge import focus_window as _fw
                import time
                for hwnd in reversed(hwnds):
                    _fw(hwnd)
                    time.sleep(0.15)
                from PySide6.QtCore import QTimer
                QTimer.singleShot(0, lambda: self._status.setText("✅ Ordre appliqué"))
            except Exception:
                from PySide6.QtCore import QTimer
                QTimer.singleShot(0, lambda: self._status.setText("✅ Sauvegardé"))
            return

        import ctypes, time
        # 1. Dégrouper chaque fenêtre (AppUserModelId unique)
        try:
            import ctypes.wintypes as wt
            class _GUID(ctypes.Structure):
                _fields_ = [("Data1",ctypes.c_ulong),("Data2",ctypes.c_ushort),
                             ("Data3",ctypes.c_ushort),("Data4",ctypes.c_ubyte*8)]
            class _PK(ctypes.Structure):
                _fields_ = [("fmtid",_GUID),("pid",ctypes.c_ulong)]
            class _PV(ctypes.Structure):
                _fields_ = [("vt",ctypes.c_ushort),("p1",ctypes.c_ushort),
                             ("p2",ctypes.c_ushort),("p3",ctypes.c_ushort),
                             ("ptr",ctypes.c_void_p)]
            VT_LPWSTR, VT_EMPTY = 31, 0
            IID = _GUID()
            IID.Data1=0x886D8EEB;IID.Data2=0x8CF2;IID.Data3=0x4446
            for i,b in enumerate([0x8D,0x02,0xCD,0xBA,0x1D,0xBD,0xCF,0x99]):
                IID.Data4[i]=b
            PK = _PK()
            PK.fmtid.Data1=0x9F4C2855;PK.fmtid.Data2=0x9F79;PK.fmtid.Data3=0x4B39
            for i,b in enumerate([0xA8,0xD0,0xE1,0xD4,0x2D,0xE1,0xD5,0xF3]):
                PK.fmtid.Data4[i]=b
            PK.pid=5
            sh = ctypes.windll.shell32
            sh.SHGetPropertyStoreForWindow.restype  = ctypes.HRESULT
            sh.SHGetPropertyStoreForWindow.argtypes = [
                wt.HWND, ctypes.POINTER(_GUID), ctypes.POINTER(ctypes.c_void_p)]

            def _set_aumi(hwnd, app_id):
                ps = ctypes.c_void_p()
                if sh.SHGetPropertyStoreForWindow(hwnd, ctypes.byref(IID), ctypes.byref(ps)) != 0:
                    return
                if not ps.value: return
                vtbl = ctypes.cast(ctypes.cast(ps.value,ctypes.POINTER(ctypes.c_void_p))[0],
                                   ctypes.POINTER(ctypes.c_void_p))
                Release  = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtbl[2])
                SetValue = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p,
                               ctypes.POINTER(_PK), ctypes.POINTER(_PV))(vtbl[6])
                Commit   = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p)(vtbl[7])
                pv = _PV()
                if app_id:
                    buf = ctypes.create_unicode_buffer(app_id)
                    pv.vt = VT_LPWSTR
                    pv.ptr = ctypes.cast(buf, ctypes.c_void_p).value
                else:
                    pv.vt = VT_EMPTY
                if SetValue(ps.value, ctypes.byref(PK), ctypes.byref(pv)) == 0:
                    Commit(ps.value)
                Release(ps.value)

            # Dégrouper
            for i, hwnd in enumerate(hwnds):
                _set_aumi(hwnd, f"DofusRetro.Char.{hwnd}")
            time.sleep(0.3)
            # Z-order
            SWP = 0x0010|0x0002|0x0001
            for i in range(len(hwnds)-1):
                try: ctypes.windll.user32.SetWindowPos(hwnds[i], hwnds[i+1], 0,0,0,0, SWP)
                except: pass
                time.sleep(0.05)
            time.sleep(0.2)
            # Regrouper
            for hwnd in hwnds:
                _set_aumi(hwnd, "DofusRetro.SharedGroup")
        except Exception as e:
            print(f"[reorder] {e}")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self._status.setText("✅ Ordre appliqué"))

    # ── Profils d'ordre ────────────────────────────────────

    def _refresh_profile_combo(self):
        self._profile_combo.clear()
        if not self._profiles:
            self._profile_combo.addItem("(aucun profil)")
        else:
            for name in self._profiles:
                self._profile_combo.addItem(name)
            # Restaurer le profil actif sauvegardé
            active = self._cfg.get("active_profile", "")
            if active:
                idx = self._profile_combo.findText(active)
                if idx >= 0:
                    self._profile_combo.setCurrentIndex(idx)

    def _apply_profile(self):
        name = self._profile_combo.currentText()
        if name not in self._profiles: return
        pseudos = self._profiles[name]
        pw = {w.pseudo: w for w in self._windows}
        ordered = [pw[p] for p in pseudos if p in pw]
        rest    = [w for w in self._windows if w.pseudo not in pseudos]
        self._windows = ordered + rest
        self._cfg["active_profile"] = name
        self._on_save()
        self._render()
        self._status.setText(f"✅ Profil «{name}» appliqué")

    def _on_profile_selected(self, name: str):
        if name in self._profiles:
            self._cfg["active_profile"] = name
            self._on_save()

    def _save_profile(self):
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel)
        import theme as T

        dlg = QDialog(self)
        dlg.setWindowTitle("Sauvegarder le profil")
        dlg.setFixedWidth(280)
        dlg.setStyleSheet(f"QDialog{{background:{T.BG};}}")
        lay = QVBoxLayout(dlg); lay.setContentsMargins(16,14,16,14); lay.setSpacing(10)

        lbl = QLabel("Nom du profil :")
        lbl.setStyleSheet(f"background:transparent;color:{T.TEXT};font-size:10pt;font-weight:bold;")
        lay.addWidget(lbl)

        inp = QLineEdit()
        inp.setPlaceholderText("Ex: Farm Arakne, Boss Donjon…")
        inp.setFixedHeight(32)
        inp.setStyleSheet(
            f"QLineEdit{{background:{T.SURFACE};color:{T.TEXT};border:none;"
            f"padding:4px 8px;font-size:10pt;}}"
            f"QLineEdit:focus{{border-bottom:2px solid {T.ORANGE};}}")
        lay.addWidget(inp)

        btns = QHBoxLayout(); btns.setSpacing(6)
        btn_ok = QPushButton("💾 Sauvegarder")
        btn_ok.setFixedHeight(32)
        btn_ok.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
            f"padding:4px 12px;font-size:9pt;font-weight:bold;}}"
            f"QPushButton:hover{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {T.GRAD1},stop:1 {T.GRAD2});}}")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setFixedHeight(32)
        btn_cancel.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};border:none;"
            f"padding:4px 12px;font-size:9pt;}}"
            f"QPushButton:hover{{color:{T.TEXT};}}")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btns.addWidget(btn_ok); btns.addWidget(btn_cancel)
        lay.addLayout(btns)

        btn_ok.clicked.connect(dlg.accept)
        btn_cancel.clicked.connect(dlg.reject)
        inp.returnPressed.connect(dlg.accept)
        inp.setFocus()

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        name = inp.text().strip()
        if not name: return

        self._profiles[name] = [w.pseudo for w in self._windows]
        self._cfg["order_profiles"] = self._profiles
        self._on_save()
        self._refresh_profile_combo()
        idx = self._profile_combo.findText(name)
        if idx >= 0: self._profile_combo.setCurrentIndex(idx)
        self._status.setText(f"✅ Profil «{name}» sauvegardé")

    def _delete_profile(self):
        name = self._profile_combo.currentText()
        if name not in self._profiles: return
        del self._profiles[name]
        self._cfg["order_profiles"] = self._profiles
        self._on_save()
        self._refresh_profile_combo()

    # ── Polling ────────────────────────────────────────────


    def set_compact(self, compact: bool):
        """Mode compact : une ligne par fenêtre, sans header ni footer."""
        self._compact = compact
        self._hdr.setVisible(not compact)
        self._ftr.setVisible(not compact)
        self._btn_save_order.setVisible(not compact)
        self._prof_frame.setVisible(not compact)
        if compact:
            for i in range(self._clay.count() - 1, -1, -1):
                item = self._clay.itemAt(i)
                if item and item.spacerItem():
                    self._clay.removeItem(item)
            n = max(1, len(self._windows))
            self._scroll.setFixedHeight(min(n * 30, 400))
        else:
            has_stretch = any(
                self._clay.itemAt(i) and self._clay.itemAt(i).spacerItem()
                for i in range(self._clay.count())
            )
            if not has_stretch:
                self._clay.addStretch()
            self._scroll.setFixedHeight(490)
        self._render()

    def _start_poll(self):
        self._discover()
        # Appliquer le profil actif au lancement si défini
        active = self._cfg.get("active_profile", "")
        if active and active in self._profiles:
            pseudos = self._profiles[active]
            pw = {w.pseudo: w for w in self._windows}
            ordered = [pw[p] for p in pseudos if p in pw]
            rest    = [w for w in self._windows if w.pseudo not in pseudos]
            self._windows = ordered + rest
            self._render()
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._discover)
        self._poll_timer.start(3000)

    # ── Navigation externe ─────────────────────────────────

    def cycle(self, direction: int):
        # Construire la liste des sessions disponibles (chargement toujours inclus)
        pool = [w for w in self._windows
                if w.loading or w.pseudo not in self._excluded]
        if not pool:
            return
        current_hwnd = foreground_handle()
        self._prev_hwnd = current_hwnd
        # Trouver la position courante dans le pool
        pos = next((i for i, w in enumerate(pool) if w.hwnd == current_hwnd), None)
        # Calculer la prochaine position
        target = (0 if pos is None else (pos + direction) % len(pool))
        chosen = pool[target]
        activate_window(chosen.hwnd)
        self.set_active(chosen.pseudo)
        self.char_switched.emit(chosen.hwnd)

    def set_active(self, pseudo: str | None):
        if self._active_pseudo == pseudo:
            return  # pas de changement, rien à faire
        old_pseudo = self._active_pseudo
        self._active_pseudo = pseudo
        # Mettre à jour uniquement les lignes concernées (pas de redraw complet)
        for i in range(self._clay.count()):
            item = self._clay.itemAt(i)
            row = item.widget() if item else None
            if not row or not hasattr(row, '_win'):
                continue
            p = row._win.pseudo
            if p == pseudo or p == old_pseudo:
                is_active = (p == pseudo)
                hl = (self._drag_idx == row._idx)
                if hl:
                    bg = '#2a1e0e'
                elif is_active:
                    bg = '#1a2a1a'
                else:
                    bg = T.SURFACE
                border_l = "border-left:3px solid #5a9a5a;" if (is_active and not hl) else ""
                row.setStyleSheet(
                    f"QFrame{{background:{bg};border:none;{border_l}}}"
                    f"QFrame:hover{{background:{T.SURFACE2};}}"
                    f"QFrame QLabel{{border:none;background:transparent;}}"
                    f"QFrame QPushButton{{border:none;}}")

    def go_main(self):
        if not self._main:
            return
        for w in self._windows:
            if w.pseudo == self._main:
                activate_window(w.hwnd)
                self.set_active(w.pseudo)
                return

    def go_prev(self):
        if self._prev_hwnd:
            activate_window(self._prev_hwnd)

    def get_ordered_hwnds(self) -> list[int]:
        return [w.hwnd for w in self._windows if w.pseudo not in self._excluded]
