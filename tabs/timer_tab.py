"""tabs/timer_tab.py — Timer PySide6."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal
import model, theme

T = theme

POS_H = ['Gauche', 'Milieu', 'Droite']
POS_V = ['Haut',   'Centre', 'Bas']

def _pos_btn(text, active, callback):
    b = QPushButton(text)
    b.setFixedHeight(22)
    b.setStyleSheet(
        f"QPushButton{{background:{'#d9791f' if active else '#d6c9b0'};"
        f"color:{'white' if active else '#7a6a56'};"
        f"border:none;border-radius:3px;padding:0 6px;font-size:7pt;font-weight:bold;}}"
        f"QPushButton:hover{{background:#d9791f;color:white;}}")
    b.clicked.connect(callback)
    return b


class GroupCard(QFrame):
    kill_clicked  = Signal(str, str)
    rare_clicked  = Signal(str, str)
    reset_clicked = Signal(str, str)

    def __init__(self, map_name, group_name, group_data, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._map_name   = map_name
        self._group_name = group_name
        self._alert      = False
        # Position sauvegardée
        self._pos_h = group_data.get('pos_h', 'Milieu')
        self._pos_v = group_data.get('pos_v', 'Centre')
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(5)

        # Ligne haut : nom + timer
        top = QHBoxLayout()
        self._name_lbl = QLabel(self._group_name)
        self._name_lbl.setStyleSheet(f"color:{T.SUBTEXT};font-weight:bold;font-size:8pt;background:transparent;")
        self._name_lbl.mouseDoubleClickEvent = self._rename
        self._timer_lbl = QLabel("00:00")
        self._timer_lbl.setStyleSheet(f"color:{T.ORANGE};font-size:20pt;font-weight:bold;background:transparent;")
        self._timer_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        top.addWidget(self._name_lbl)
        top.addWidget(self._timer_lbl)
        lay.addLayout(top)

        lay.addWidget(theme.sep(self))

        # Position horizontale
        h_row = QHBoxLayout(); h_row.setSpacing(3)
        lbl_h = QLabel("Position :")
        lbl_h.setStyleSheet(f"color:{T.HINT};font-size:7pt;background:transparent;")
        h_row.addWidget(lbl_h)
        self._h_btns = {}
        for h in POS_H:
            b = _pos_btn(h, h == self._pos_h, lambda _, hv=h: self._set_pos_h(hv))
            h_row.addWidget(b)
            self._h_btns[h] = b
        h_row.addStretch()
        lay.addLayout(h_row)

        # Position verticale
        v_row = QHBoxLayout(); v_row.setSpacing(3)
        lbl_v = QLabel("                ")  # alignement
        lbl_v.setStyleSheet("background:transparent;")
        v_row.addWidget(lbl_v)
        self._v_btns = {}
        for v in POS_V:
            b = _pos_btn(v, v == self._pos_v, lambda _, vv=v: self._set_pos_v(vv))
            v_row.addWidget(b)
            self._v_btns[v] = b
        v_row.addStretch()
        lay.addLayout(v_row)

        lay.addWidget(theme.sep(self))

        # Boutons action
        btns = QHBoxLayout(); btns.setSpacing(6)
        self._btn_kill = QPushButton("KILL")
        self._btn_kill.setObjectName("btn_green")
        self._btn_kill.clicked.connect(lambda: self.kill_clicked.emit(self._group_name, self._map_name))
        self._btn_rare = QPushButton("RARE")
        self._btn_rare.setObjectName("btn_blue")
        self._btn_rare.clicked.connect(lambda: self.rare_clicked.emit(self._group_name, self._map_name))
        self._btn_reset = QPushButton("↺")
        self._btn_reset.setObjectName("btn_orange")
        self._btn_reset.setFixedWidth(36)
        self._btn_reset.clicked.connect(lambda: self.reset_clicked.emit(self._group_name, self._map_name))
        btns.addWidget(self._btn_kill)
        btns.addWidget(self._btn_rare)
        btns.addWidget(self._btn_reset)
        lay.addLayout(btns)

    def _rename(self, event):
        name, ok = QInputDialog.getText(self, "Renommer", "Nouveau nom :", text=self._group_name)
        if ok and name.strip():
            self._group_name = name.strip()
            self._name_lbl.setText(name.strip())

    def _set_pos_h(self, val):
        self._pos_h = val
        for h, b in self._h_btns.items():
            active = (h == val)
            b.setStyleSheet(
                f"QPushButton{{background:{'#d9791f' if active else '#d6c9b0'};"
                f"color:{'white' if active else '#7a6a56'};"
                f"border:none;border-radius:3px;padding:0 6px;font-size:7pt;font-weight:bold;}}"
                f"QPushButton:hover{{background:#d9791f;color:white;}}")
        self._save_pos()

    def _set_pos_v(self, val):
        self._pos_v = val
        for v, b in self._v_btns.items():
            active = (v == val)
            b.setStyleSheet(
                f"QPushButton{{background:{'#d9791f' if active else '#d6c9b0'};"
                f"color:{'white' if active else '#7a6a56'};"
                f"border:none;border-radius:3px;padding:0 6px;font-size:7pt;font-weight:bold;}}"
                f"QPushButton:hover{{background:#d9791f;color:white;}}")
        self._save_pos()

    def _save_pos(self):
        cfg = model.load_config()
        key = f"pos_{self._map_name}_{self._group_name}"
        cfg[key] = {'pos_h': self._pos_h, 'pos_v': self._pos_v}
        model.save_config(cfg)

    def update_timer(self, elapsed):
        if elapsed is None:
            self._timer_lbl.setText("00:00")
            self._set_alert(False)
            return
        elapsed = int(elapsed)
        m, s = divmod(elapsed, 60)
        self._timer_lbl.setText(f"{m:02d}:{s:02d}")
        self._set_alert(elapsed >= model.get_alert_threshold())

    def _set_alert(self, alert):
        if alert == self._alert:
            return
        self._alert = alert
        color = T.RED if alert else T.ORANGE
        self._timer_lbl.setStyleSheet(f"color:{color};font-size:20pt;font-weight:bold;background:transparent;")
        self.setStyleSheet(
            f"QFrame#card{{border:2px solid {T.RED};border-radius:4px;background:{T.SURFACE};}}"
            if alert else "")


class MapPanel(QWidget):
    def __init__(self, map_name, map_data, callbacks, parent=None):
        super().__init__(parent)
        self._map_name  = map_name
        self._callbacks = callbacks
        self._cards     = {}
        self._build(map_data)

    def _build(self, map_data):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(6)
        cfg = model.load_config()
        for group_name, group_data in map_data['groups'].items():
            # Restaurer la position sauvegardée
            key = f"pos_{self._map_name}_{group_name}"
            pos = cfg.get(key, {})
            group_data['pos_h'] = pos.get('pos_h', 'Milieu')
            group_data['pos_v'] = pos.get('pos_v', 'Centre')
            card = GroupCard(self._map_name, group_name, group_data)
            card.kill_clicked.connect(self._callbacks['on_kill'])
            card.rare_clicked.connect(self._callbacks['on_bambouto'])
            card.reset_clicked.connect(self._callbacks['on_reset_group'])
            lay.addWidget(card)
            self._cards[group_name] = card
        lay.addStretch()

    def update_timers(self, map_data):
        for gname, card in self._cards.items():
            gd = map_data['groups'].get(gname, {})
            card.update_timer(model.elapsed_seconds(gd))


class TimerTab(QWidget):
    def __init__(self, maps, callbacks, parent=None):
        super().__init__(parent)
        self._maps        = maps
        self._callbacks   = callbacks
        self._panels      = {}
        self._current_map = list(maps.keys())[0] if maps else None
        self._map_bar_lay = None
        self._build()
        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._tick)
        self._tick_timer.start(500)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        # Stats
        stats = QFrame(); stats.setObjectName("card")
        sl = QVBoxLayout(stats); sl.setContentsMargins(12, 8, 12, 8); sl.setSpacing(4)
        self._kill_lbl = QLabel("Kill  —")
        self._rare_lbl = QLabel("Rare  —")
        for l in (self._kill_lbl, self._rare_lbl):
            l.setStyleSheet(f"color:{T.SUBTEXT};font-size:9pt;background:transparent;")
        sl.addWidget(self._kill_lbl)
        sl.addWidget(theme.sep(stats))
        sl.addWidget(self._rare_lbl)
        lay.addWidget(stats)

        # Barre maps
        map_bar_wrap = QHBoxLayout(); map_bar_wrap.setSpacing(3)
        self._map_bar_wrap = map_bar_wrap

        self._map_btns_frame = QFrame()
        self._map_bar_lay = QHBoxLayout(self._map_btns_frame)
        self._map_bar_lay.setContentsMargins(0,0,0,0)
        self._map_bar_lay.setSpacing(3)
        self._map_btns = {}

        for map_name in self._maps:
            self._add_map_btn(map_name)

        map_bar_wrap.addWidget(self._map_btns_frame)
        map_bar_wrap.addStretch()

        btn_add = QPushButton("+"); btn_add.setObjectName("btn_green"); btn_add.setFixedWidth(28)
        btn_add.clicked.connect(self._on_add_map)
        btn_del = QPushButton("−"); btn_del.setObjectName("btn_red"); btn_del.setFixedWidth(28)
        btn_del.clicked.connect(self._on_delete_map)
        map_bar_wrap.addWidget(btn_add)
        map_bar_wrap.addWidget(btn_del)
        lay.addLayout(map_bar_wrap)

        # Panneau renommage inline (caché par défaut)
        self._rename_panel = QFrame()
        self._rename_panel.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};border-radius:4px;}}")
        rp_lay = QHBoxLayout(self._rename_panel)
        rp_lay.setContentsMargins(10, 8, 10, 8); rp_lay.setSpacing(6)

        from PySide6.QtWidgets import QLineEdit
        lbl_r = QLabel("Nom de la map :")
        lbl_r.setStyleSheet(f"color:{T.HINT};font-size:8pt;font-weight:bold;background:transparent;")
        self._rename_input = QLineEdit()
        self._rename_input.setStyleSheet(
            f"QLineEdit{{background:{T.SURFACE2};border:1px solid {T.BORDER};border-radius:3px;"
            f"padding:4px 8px;color:{T.TEXT};font-size:9pt;}}"
            f"QLineEdit:focus{{border-color:{T.ORANGE};}}")
        self._rename_input.returnPressed.connect(self._confirm_rename)

        btn_ok = QPushButton("✔")
        btn_ok.setFixedWidth(32)
        btn_ok.setStyleSheet(
            f"QPushButton{{background:{T.GREEN};color:white;border:none;border-radius:3px;"
            f"padding:5px;font-weight:bold;font-size:10pt;}}"
            f"QPushButton:hover{{background:#6e9428;}}")
        btn_ok.clicked.connect(self._confirm_rename)

        btn_cancel = QPushButton("✕")
        btn_cancel.setFixedWidth(32)
        btn_cancel.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};border:1px solid {T.BORDER};"
            f"border-radius:3px;padding:5px;font-weight:bold;}}"
            f"QPushButton:hover{{border-color:{T.RED};color:{T.RED};}}")
        btn_cancel.clicked.connect(self._cancel_rename)

        rp_lay.addWidget(lbl_r)
        rp_lay.addWidget(self._rename_input, 1)
        rp_lay.addWidget(btn_ok)
        rp_lay.addWidget(btn_cancel)
        self._rename_panel.hide()
        lay.addWidget(self._rename_panel)

        # Panels
        self._panels_widget = QWidget()
        self._panels_lay = QVBoxLayout(self._panels_widget)
        self._panels_lay.setContentsMargins(0, 0, 0, 0)
        for map_name, map_data in self._maps.items():
            panel = MapPanel(map_name, map_data, self._callbacks)
            self._panels[map_name] = panel
            self._panels_lay.addWidget(panel)
            panel.hide()
        lay.addWidget(self._panels_widget)

        if self._current_map:
            self._switch_map(self._current_map)

    def _add_map_btn(self, map_name):
        btn = QPushButton(map_name)
        btn.clicked.connect(lambda _, n=map_name: self._switch_map(n))
        btn.mouseDoubleClickEvent = lambda e, n=map_name: self._open_rename(n)
        self._map_bar_lay.addWidget(btn)
        self._map_btns[map_name] = btn

    def _switch_map(self, name):
        self._current_map = name
        for n, p in self._panels.items():
            p.setVisible(n == name)
        for n, b in self._map_btns.items():
            active = (n == name)
            b.setObjectName("btn_orange" if active else "")
            b.style().unpolish(b); b.style().polish(b)

    def _open_rename(self, name):
        self._renaming = name
        self._rename_input.setText(name)
        self._rename_input.selectAll()
        self._rename_panel.show()
        self._rename_panel.setVisible(True)
        self._rename_input.setFocus()
        self._fit()

    def _confirm_rename(self):
        new_name = self._rename_input.text().strip()
        if new_name and new_name != self._renaming:
            cb = self._callbacks.get('on_rename_map')
            if cb: cb(self._renaming, new_name)
        self._cancel_rename()

    def _cancel_rename(self):
        self._rename_panel.hide()
        self._fit()

    def _fit(self):
        root = self.window()
        if not root or not hasattr(root, '_adjust_height'): return
        root._adjust_height()

    def _on_add_map(self):
        cb = self._callbacks.get('on_add_map')
        if cb: cb()

    def _on_delete_map(self):
        cb = self._callbacks.get('on_delete_map')
        if cb: cb()

    def _tick(self):
        if self._current_map and self._current_map in self._panels:
            panel = self._panels[self._current_map]
            # Utiliser la référence live du dict maps
            map_data = self._maps.get(self._current_map, {})
            if map_data:
                panel.update_timers(map_data)

    def update_stats(self, kill_text, rare_text):
        self._kill_lbl.setText(kill_text)
        self._rare_lbl.setText(rare_text)

    def add_map(self, map_name, map_data):
        """Appelé depuis main_window quand une map est ajoutée."""
        self._add_map_btn(map_name)
        panel = MapPanel(map_name, map_data, self._callbacks)
        self._panels[map_name] = panel
        self._panels_lay.addWidget(panel)
        panel.hide()
        self._switch_map(map_name)

    def remove_map(self, map_name):
        """Appelé depuis main_window quand une map est supprimée."""
        if map_name in self._map_btns:
            btn = self._map_btns.pop(map_name)
            self._map_bar_lay.removeWidget(btn)
            btn.deleteLater()
        if map_name in self._panels:
            panel = self._panels.pop(map_name)
            panel.deleteLater()
        # Basculer sur la première map restante
        if self._maps:
            first = list(self._maps.keys())[0]
            self._switch_map(first)

    def rename_map(self, old_name, new_name):
        """Met à jour le bouton après renommage."""
        if old_name in self._map_btns:
            btn = self._map_btns.pop(old_name)
            btn.setText(new_name)
            btn.clicked.disconnect()
            btn.clicked.connect(lambda _, n=new_name: self._switch_map(n))
            btn.mouseDoubleClickEvent = lambda e, n=new_name: self._open_rename(n)
            self._map_btns[new_name] = btn
        if old_name in self._panels:
            self._panels[new_name] = self._panels.pop(old_name)
        self._current_map = new_name
