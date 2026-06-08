"""tabs/accounts_tab.py — Outil multi-comptes Dofus Rétro."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QSizePolicy, QStackedWidget
)
from PySide6.QtCore import Qt, QTimer, QSize, Signal
import model, theme as T

from tabs.accounts.characters_panel import AccountPanel
from tabs.accounts.shortcuts_panel   import ShortcutsPanel
from tabs.accounts.settings_panel    import ConfigPanel
from tabs.accounts.hotkey_manager    import ShortcutTable
from tabs.accounts.toast_reader      import make_watcher, AlertEvent
from tabs.accounts.window_manager    import activate_window, is_game_focused
from tabs.accounts.move_mode         import SwitchModeCtrl
from tabs.accounts.notif_help        import AlertGuideDialog

CFG_KEY = "accounts_config"

_NOTIF_COLORS = {
    "combat": T.RED,  "pvp":    T.RED,
    "echange": T.BLUE, "mp":    T.ORANGE,
    "groupe":  T.GREEN, "defi": T.GOLD,
    "craft":   T.GREEN,
}


def _tab_btn(label: str, active: bool) -> QPushButton:
    b = QPushButton(label)
    b.setCheckable(True); b.setChecked(active)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    ss_active = (
        f"QPushButton{{background:{T.SURFACE};color:{T.ORANGE};"
        f"border:none;border-top:2px solid {T.ORANGE};"
        f"padding:7px 4px;font-size:8pt;font-weight:bold;}}")
    ss_idle = (
        f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
        f"border:none;border-top:2px solid transparent;"
        f"padding:7px 4px;font-size:8pt;font-weight:bold;}}"
        f"QPushButton:hover{{color:{T.TEXT};}}")
    b.setStyleSheet(ss_active if active else ss_idle)
    return b


class AccountsTab(QWidget):

    _notif_received = Signal(object)
    _do_next        = Signal()
    _do_prev        = Signal()
    _do_main        = Signal()
    _do_back        = Signal()
    _do_cs          = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._cfg = model.load_config().get(CFG_KEY, {})
        self._reg = ShortcutTable()
        self._farm_mode = False
        # Farm Sadi manager
        from tabs.accounts.hotkey_manager import CycleEngine
        fs = self._cfg.get("farmsadi", {})
        self._farmsadi = CycleEngine(turns=fs.get("turns", 3))
        self._farmsadi.set_sadis(set(fs.get("sadis", [])))
        self._move_mgr  = SwitchModeCtrl(
            cycle_fn=self._next,
            on_state_change=self._on_move_state)
        self._build()
        self._notif_received.connect(self._show_notif)
        self._do_next.connect(self._next_safe)
        self._do_prev.connect(self._prev_safe)
        self._do_main.connect(self._main_safe)
        self._do_back.connect(self._back_safe)
        self._do_cs.connect(self._cs_safe)
        self._start_watcher()
        # Réappliquer les raccourcis après démarrage event loop
        QTimer.singleShot(500, self._sc._load_and_apply)
        # Maximiser les fenêtres Dofus si option activée
        QTimer.singleShot(1500, self._apply_maximize_on_launch)
        # Raccourci mode déplacement
        move_sc = self._cfg.get("shortcuts", {}).get("move_mode", "")
        if move_sc:
            self._reg.add("move_mode", move_sc, self._toggle_move_mode)

    # ── Construction ───────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Bandeau notification toast ─────────────────────
        self._notif_bar = QFrame()
        self._notif_bar.setStyleSheet(f"QFrame{{background:{T.ORANGE};border:none;}}")
        nbl = QHBoxLayout(self._notif_bar)
        nbl.setContentsMargins(10, 4, 10, 4); nbl.setSpacing(6)
        self._n_icon = QLabel("🔔")
        self._n_icon.setStyleSheet("background:transparent;font-size:11pt;")
        self._n_text = QLabel("")
        self._n_text.setStyleSheet(
            "background:transparent;color:white;font-size:8pt;font-weight:bold;")
        self._n_text.setWordWrap(True)
        btn_x = QPushButton("✕")
        btn_x.setFixedSize(18, 18)
        btn_x.setStyleSheet(
            "QPushButton{background:transparent;color:white;border:none;font-size:9pt;}"
            "QPushButton:hover{color:#ffccaa;}")
        btn_x.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_x.clicked.connect(self._hide_notif)
        nbl.addWidget(self._n_icon); nbl.addWidget(self._n_text, 1); nbl.addWidget(btn_x)
        self._notif_bar.hide()
        root.addWidget(self._notif_bar)

        # ── Barre d'onglets ────────────────────────────────
        tbar = QFrame()
        tbar.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border-bottom:1px solid {T.BORDER};}}")
        tbl = QHBoxLayout(tbar); tbl.setContentsMargins(4,4,4,4); tbl.setSpacing(3)
        self._tab_btns = []
        _btn_w = 100  # largeur fixe identique pour les 3 boutons
        for i, lbl in enumerate(["👥 Personnages", "⌨ Raccourcis", "⚙ Paramètres"]):
            btn = QPushButton(lbl)
            btn.setCheckable(True); btn.setChecked(i == 0)
            btn.setFixedHeight(26)
            btn.setFixedWidth(_btn_w)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            ss_on = (
                f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;"
                f"border:2px solid transparent;border-radius:8px;"
                f"font-size:8pt;font-weight:700;padding:3px 6px;}}")
            ss_off = (
                f"QPushButton{{background:{T.SURFACE};color:{T.HINT};"
                f"border:2px solid transparent;border-radius:8px;"
                f"font-size:8pt;font-weight:700;padding:3px 6px;}}"
                f"QPushButton:hover{{color:{T.TEXT};background:{T.SURFACE2};}}")
            btn.setStyleSheet(ss_on if i == 0 else ss_off)
            btn.clicked.connect(lambda _, idx=i: self._show_tab(idx))
            tbl.addWidget(btn); self._tab_btns.append(btn)

        tbl.addStretch()
        btn_help = QPushButton("Tuto")
        btn_help.setFixedHeight(26)
        btn_help.setToolTip("Tutoriel : activer les notifications Dofus")
        btn_help.setStyleSheet(
            f"QPushButton{{background:{T.SURFACE};color:{T.ORANGE};"
            f"border:none;font-size:8pt;font-weight:bold;padding:2px 8px;margin-right:4px;}}"
            f"QPushButton:hover{{background:{T.ORANGE};color:white;}}")
        btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_help.clicked.connect(lambda: AlertGuideDialog(self).exec())
        tbl.addWidget(btn_help)
        root.addWidget(tbar)

        # ── Barre Modes — 2 lignes ────────────────────────
        mbar = QFrame()
        mbar.setStyleSheet(
            f"QFrame{{background:{T.BG_DARK};border-bottom:1px solid {T.BORDER};}}")
        from PySide6.QtWidgets import QLabel as _QL
        mv = QVBoxLayout(mbar); mv.setContentsMargins(8,4,8,4); mv.setSpacing(3)

        # Ligne 1 : Mode : Farm + Déplacement
        row1 = QHBoxLayout(); row1.setSpacing(8); row1.setContentsMargins(0,0,0,0)
        lbl_mode = _QL("Mode :")
        lbl_mode.setStyleSheet(f"background:transparent;color:{T.HINT};font-size:9pt;font-weight:bold;")
        row1.addWidget(lbl_mode)

        pill_base = (
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
            f"border:1px solid {T.BORDER};border-radius:14px;"
            f"padding:3px 12px;font-size:9pt;font-weight:700;}}"
            f"QPushButton:hover{{background:{T.BORDER};color:{T.TEXT};}}"
        )
        pill_on_green = (
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;"
            f"border:none;border-radius:14px;"
            f"padding:3px 12px;font-size:9pt;font-weight:700;}}"
        )
        pill_on_blue = (
            f"QPushButton{{background:{T.BLUE};color:white;"
            f"border:none;border-radius:14px;"
            f"padding:3px 12px;font-size:9pt;font-weight:700;}}"
        )

        self._farm_btn = QPushButton("🌾 Farm OFF")
        self._farm_btn.setFixedHeight(28)
        self._farm_btn.setCheckable(True); self._farm_btn.setChecked(False)
        self._farm_btn.setStyleSheet(pill_base)
        self._farm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._farm_btn.setToolTip("Désactive l'autofocus combat sur tous les comptes")
        self._farm_btn.clicked.connect(self._toggle_farm_mode)
        row1.addWidget(self._farm_btn)

        self._move_btn = QPushButton("👟 Déplacement OFF")
        self._move_btn.setFixedHeight(28)
        self._move_btn.setCheckable(True); self._move_btn.setChecked(False)
        self._move_btn.setStyleSheet(pill_base)
        self._move_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._move_btn.setToolTip("Clic gauche sur Dofus = personnage suivant")
        self._move_btn.clicked.connect(self._toggle_move_mode)
        row1.addWidget(self._move_btn)

        self._pill_base     = pill_base
        self._pill_on_green = pill_on_green
        self._pill_on_blue  = pill_on_blue
        row1.addStretch()
        mv.addLayout(row1)

        # Ligne 2 : Sadi
        row2 = QHBoxLayout(); row2.setSpacing(8); row2.setContentsMargins(0,0,0,0)
        self._sadi_btn = QPushButton("🌿 Farm Sadi OFF")
        self._sadi_btn.setFixedHeight(28)
        self._sadi_btn.setCheckable(True); self._sadi_btn.setChecked(False)
        self._sadi_btn.setStyleSheet(self._pill_base)
        self._sadi_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._sadi_btn.setToolTip("Ignore le combat N tours pour les Sadidas cochés")
        self._sadi_btn.clicked.connect(self._toggle_sadi_mode)
        row2.addWidget(self._sadi_btn)
        row2.addStretch()
        mv.addLayout(row2)
        root.addWidget(mbar)

        # ── Panneau config Farm Sadi (caché par défaut) ────
        self._sadi_config = QFrame()
        self._sadi_config.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border-bottom:1px solid {T.BORDER};}}")
        sc_lay = QVBoxLayout(self._sadi_config)
        sc_lay.setContentsMargins(12, 8, 12, 10); sc_lay.setSpacing(8)

        # Ligne : Ignorer N tours
        from PySide6.QtWidgets import QSpinBox, QLabel as _QL2, QCheckBox
        turns_row = QHBoxLayout(); turns_row.setSpacing(8)
        for txt in []:
            pass
        lbl_t1 = _QL2("Ignorer")
        lbl_t1.setStyleSheet(f"background:transparent;color:{T.TEXT};font-size:10pt;font-weight:bold;")
        self._sadi_spin = QSpinBox()
        self._sadi_spin.setRange(1, 20)
        self._sadi_spin.setValue(self._cfg.get("farmsadi", {}).get("turns", 3))
        self._sadi_spin.setFixedWidth(56); self._sadi_spin.setFixedHeight(28)
        self._sadi_spin.setStyleSheet(
            f"QSpinBox{{background:{T.BG_DARK};color:{T.ORANGE};border:none;"
            f"padding:3px 6px;font-size:10pt;font-weight:bold;}}"
            f"QSpinBox::up-button,QSpinBox::down-button{{background:{T.BG_DARK};border:none;width:14px;}}")
        self._sadi_spin.valueChanged.connect(self._on_sadi_turns_change)
        lbl_t2 = _QL2("tours de combat avant autofocus")
        lbl_t2.setStyleSheet(f"background:transparent;color:{T.TEXT};font-size:9pt;")
        turns_row.addWidget(lbl_t1); turns_row.addWidget(self._sadi_spin); turns_row.addWidget(lbl_t2); turns_row.addStretch()
        sc_lay.addLayout(turns_row)

        # Persos Sadida
        lbl_ch = _QL2("Cocher les Sadidas concernés :")
        lbl_ch.setStyleSheet(f"background:transparent;color:{T.HINT};font-size:9pt;font-style:italic;")
        sc_lay.addWidget(lbl_ch)
        self._sadi_chars_lay = QVBoxLayout(); self._sadi_chars_lay.setSpacing(3)
        sc_lay.addLayout(self._sadi_chars_lay)
        self._sadi_config.hide()
        root.addWidget(self._sadi_config)

        # ── Stack ──────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        self._chars = AccountPanel(self._cfg, self._save)
        self._sc    = ShortcutsPanel(
            self._cfg, self._reg, self._save,
            on_next       = self._next,
            on_prev       = self._prev,
            on_main       = self._main,
            on_back       = self._back,
            on_ctrl_shift = self._toggle_cs,
        )
        self._sets = ConfigPanel(self._cfg, self._save)

        for p in (self._chars, self._sc, self._sets):
            self._stack.addWidget(p)
        root.addWidget(self._stack)

    def _show_tab(self, idx: int):
        self._stack.setCurrentIndex(idx)
        ss_on = (
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;"
            f"border:2px solid transparent;border-radius:8px;"
            f"font-size:8pt;font-weight:700;padding:3px 6px;}}")
        ss_off = (
            f"QPushButton{{background:{T.SURFACE};color:{T.HINT};"
            f"border:2px solid transparent;border-radius:8px;"
            f"font-size:8pt;font-weight:700;padding:3px 6px;}}"
            f"QPushButton:hover{{color:{T.TEXT};background:{T.SURFACE2};}}")
        for i, btn in enumerate(self._tab_btns):
            btn.setChecked(i == idx)
            btn.setStyleSheet(ss_on if i == idx else ss_off)
        self._fit()

    # ── Navigation ─────────────────────────────────────────

    # Appelés depuis thread keyboard → émettent un signal vers le thread Qt
    def _next(self): self._do_next.emit()
    def _prev(self): self._do_prev.emit()
    def _main(self): self._do_main.emit()
    def _back(self): self._do_back.emit()

    # Exécutés sur le thread Qt principal
    def _next_safe(self):
        self._chars.cycle(+1)
        self._reg.ctrl_shift.sync_keys()

    def _prev_safe(self):
        self._chars.cycle(-1)
        self._reg.ctrl_shift.sync_keys()

    def _main_safe(self):
        self._chars.go_main()
        self._reg.ctrl_shift.sync_keys()

    def _back_safe(self):
        self._chars.go_prev()

    def _apply_maximize_on_launch(self):
        if not self._sets.get("maximize_on_launch", False):
            return
        try:
            from tabs.accounts.window_manager import collect_sessions, _W32
            if not _W32: return
            import win32gui, win32con
            for w in collect_sessions():
                try:
                    win32gui.ShowWindow(w.hwnd, win32con.SW_MAXIMIZE)
                except Exception:
                    pass
        except Exception:
            pass

    def _toggle_farm_mode(self):
        self._farm_mode = self._farm_btn.isChecked()
        self._farm_btn.setText("🌾 Farm ON" if self._farm_mode else "🌾 Farm OFF")
        self._farm_btn.setStyleSheet(
            self._pill_on_green if self._farm_mode else self._pill_base)

    def _toggle_move_mode(self):
        self._move_mgr.toggle()

    def _on_move_state(self, active: bool):
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self._update_move_btn(active))

    def _update_move_btn(self, active: bool):
        self._move_btn.setChecked(active)
        self._move_btn.setText("👟 Déplacement ON" if active else "👟 Déplacement OFF")
        self._move_btn.setStyleSheet(
            self._pill_on_blue if active else self._pill_base)

    def _toggle_sadi_mode(self):
        on = self._sadi_btn.isChecked()
        self._sadi_btn.setText("🌿 Sadi ON" if on else "🌿 Sadi OFF")
        self._sadi_btn.setStyleSheet(
            self._pill_on_green if on else self._pill_base)
        self._cfg.setdefault("farmsadi", {})["enabled"] = on
        if on:
            self._refresh_sadi_chars()
            self._sadi_config.show()
        else:
            self._sadi_config.hide()
            self._farmsadi.cancel_all()
        self._save(); self._fit()

    def _refresh_sadi_chars(self):
        from PySide6.QtWidgets import QCheckBox, QLabel
        while self._sadi_chars_lay.count():
            item = self._sadi_chars_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        sadis = set(self._cfg.get("farmsadi", {}).get("sadis", []))
        windows = getattr(self._chars, '_windows', [])
        if not windows:
            lbl = QLabel("Aucun perso détecté — ouvre Dofus d'abord")
            lbl.setStyleSheet(f"background:transparent;color:{T.HINT};font-size:9pt;font-style:italic;")
            self._sadi_chars_lay.addWidget(lbl); return
        for win in windows:
            cb = QCheckBox(win.pseudo)
            cb.setChecked(win.pseudo in sadis)
            cb.setStyleSheet(
                f"QCheckBox{{color:{T.TEXT};font-size:10pt;background:transparent;spacing:8px;}}"
                f"QCheckBox::indicator{{width:16px;height:16px;background:{T.BG_DARK};border:none;}}"
                f"QCheckBox::indicator:checked{{background:#5a8a5a;}}")
            cb.toggled.connect(lambda v, p=win.pseudo: self._on_sadi_char_toggle(p, v))
            self._sadi_chars_lay.addWidget(cb)

    def _on_sadi_char_toggle(self, pseudo: str, checked: bool):
        sadis = set(self._cfg.get("farmsadi", {}).get("sadis", []))
        if checked: sadis.add(pseudo)
        else: sadis.discard(pseudo); self._farmsadi.cancel(pseudo)
        self._cfg.setdefault("farmsadi", {})["sadis"] = list(sadis)
        self._farmsadi.set_sadis(sadis); self._save()

    def _on_sadi_turns_change(self, val: int):
        self._farmsadi.turns = val
        self._cfg.setdefault("farmsadi", {})["turns"] = val; self._save()

    def _toggle_cs(self): self._do_cs.emit()

    def _cs_safe(self):
        active = self._reg.ctrl_shift.toggle()
        self._sc.update_cs_indicator(active)

    # ── Toast notifications ────────────────────────────────

    def _start_watcher(self):
        remove = self._cfg.get("settings", {}).get("remove_notif_after_read", True)
        self._watcher = make_watcher(self._on_notif, remove=remove)
        self._watcher.start()

    def _on_notif(self, notif: AlertEvent):
        # Signal thread-safe — appelé depuis le thread winsdk
        self._notif_received.emit(notif)

    def _show_notif(self, notif: AlertEvent):
        if not notif: return

        key          = f"autofocus_{notif.ntype}"
        autofocus_on = self._sets.get(key, False)
        farmsadi_on  = self._cfg.get("farmsadi", {}).get("enabled", False)
        is_combat    = notif.ntype == "combat"

        if is_combat and self._farm_mode:
            return

        if autofocus_on:
            if is_combat and farmsadi_on:
                skip, left = self._farmsadi.check(notif.pseudo)
                if skip:
                    self._show_banner(notif,
                        f"🌿 Farm Sadi — {left} tour{'s' if left>1 else ''} restant{'s' if left>1 else ''}")
                    return
            from tabs.accounts.window_manager import activate_by_name
            activate_by_name(notif.pseudo)
            self._chars.set_active(notif.pseudo)
        elif is_combat and farmsadi_on:
            skip, left = self._farmsadi.check(notif.pseudo)
            if skip:
                self._show_banner(notif,
                    f"🌿 Farm Sadi — {left} tour{'s' if left>1 else ''} restant{'s' if left>1 else ''}")
        # Sinon : ignorer complètement, aucun bandeau

    def _show_banner(self, notif: "AlertEvent", text: str):
        color = _NOTIF_COLORS.get(notif.ntype, T.ORANGE)
        self._notif_bar.setStyleSheet(f"QFrame{{background:{color};border:none;}}")
        self._n_icon.setText(notif.emoji)
        self._n_text.setText(f"[{notif.pseudo}]  {text}")
        self._notif_bar.show()
        QTimer.singleShot(5000, self._hide_notif)
        self._fit()

    def _hide_notif(self):
        self._notif_bar.hide()
        self._fit()

    # ── Persistance ────────────────────────────────────────

    def _save(self):
        model.save_config({CFG_KEY: self._cfg})

    # ── Hauteur ────────────────────────────────────────────

    def _fit(self):
        w = self
        while w:
            w.updateGeometry()
            w = w.parentWidget()
        root = self.window()
        if not root: return
        root.setMinimumHeight(0); root.setMaximumHeight(16777215)
        root.adjustSize()

    def sizeHint(self):
        cur = self._stack.currentWidget()
        h   = cur.sizeHint().height() if cur else 300
        nh  = 36 if not self._notif_bar.isHidden() else 0
        return QSize(350, 42 + nh + h)

    def closeEvent(self, e):
        self._reg.clear()
        self._watcher.stop()
        super().closeEvent(e)

    @property
    def move_mgr(self):
        return self._move_mgr
