"""
main_window.py — Fenêtre principale PySide6 de Retro Toolbox.
"""

from PySide6.QtWidgets import (QStackedWidget,
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QFileDialog, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QIcon
from pathlib import Path

import model, theme
from tabs.timer_tab      import TimerTab
from tabs.challenges_tab import ChallengesTab
from tabs.runes_tab      import RunesTab
from tabs.settings_tab   import SettingsTab
from tabs.about_tab      import AboutTab


class NavButton(QPushButton):
    """Bouton de navigation bas."""

    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setObjectName("nav_btn")
        self.setFixedHeight(56)
        self._icon_txt  = icon
        self._label_txt = label
        self.setText(f"{icon}\n{label}")
        self.setStyleSheet(f"""
            QPushButton {{
                background: {theme.BG_DARK};
                color: {theme.HINT};
                border: none;
                font-size: 9pt;
                font-weight: bold;
                padding: 4px 2px;
            }}
            QPushButton:checked {{
                background: {theme.SURFACE};
                color: {theme.ORANGE};
                border-top: 2px solid {theme.ORANGE};
            }}
            QPushButton:hover:!checked {{
                color: {theme.SUBTEXT};
            }}
        """)


class MainWindow(QMainWindow):

    WIDTH = 350

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Retro Toolbox")
        self.setFixedWidth(self.WIDTH)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint
        )

        # Icône dans toute l'application
        import sys
        from pathlib import Path
        from PySide6.QtGui import QIcon
        def _res(rel):
            if getattr(sys, 'frozen', False):
                return Path(sys._MEIPASS) / rel
            return Path(__file__).parent / rel
        icon = QIcon(str(_res("retro_toolbox.ico")))
        self.setWindowIcon(icon)
        from PySide6.QtWidgets import QApplication
        QApplication.setWindowIcon(icon)

        # Données
        self.data_file = self._resolve_data_file()
        self.maps = model.load_maps(self.data_file)

        self._build_ui()
        self._switch_tab(0)

        # Stats ticker
        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._refresh_stats)
        self._stats_timer.start(1000)

    # ── Données ───────────────────────────────────────────

    def _resolve_data_file(self):
        path = model.get_data_file_path()
        if path:
            return path
        folder = QFileDialog.getExistingDirectory(
            self, "Dossier des données", str(Path.home()))
        if not folder:
            folder = str(Path.home())
        json_path = Path(folder) / 'dofus_timers.json'
        model.set_data_file_path(json_path)
        return json_path

    def _save(self):
        try:
            model.save_maps(self.maps, self.data_file)
        except Exception as e:
            print(f"Erreur sauvegarde: {e}")

    # ── UI ────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_lay = QVBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # Titlebar
        title_bar = QFrame()
        title_bar.setFixedHeight(44)
        title_bar.setStyleSheet(f"background:{theme.BG_DARK};border-bottom:1px solid {theme.BORDER};")
        tb_lay = QHBoxLayout(title_bar)
        tb_lay.setContentsMargins(14, 0, 8, 0)

        lbl = QLabel("Retro Toolbox")
        lbl.setStyleSheet(f"font-size:12pt;font-weight:bold;color:{theme.TEXT};background:transparent;")
        tb_lay.addWidget(lbl)
        tb_lay.addStretch()
        main_lay.addWidget(title_bar)

        # Callbacks timer
        callbacks = {
            'on_kill':         self._on_kill,
            'on_bambouto':     self._on_bambouto,
            'on_reset_group':  self._on_reset_group,
            'on_add_map':      self._on_add_map,
            'on_delete_map':   self._on_delete_map,
            'on_reset_all':    self._on_reset_all,
            'on_clear_stats':  self._on_clear_stats,
            'on_rename_map':   self._on_rename_map,
        }

        # Onglets
        self._tabs = [
            TimerTab(self.maps, callbacks),
            ChallengesTab(),
            RunesTab(),
            SettingsTab(str(self.data_file), self._on_change_folder),
            AboutTab(),
        ]

        # Stack — QStackedWidget expose uniquement le widget actif pour sizeHint
        self._stack = QStackedWidget()
        self._stack.setContentsMargins(0, 0, 0, 0)
        for tab in self._tabs:
            self._stack.addWidget(tab)
        main_lay.addWidget(self._stack, 1)

        # Navbar bas
        navbar = QWidget()
        navbar.setObjectName("navbar")
        navbar.setFixedHeight(60)
        navbar.setStyleSheet(f"background:{theme.BG_DARK};border-top:1px solid {theme.BORDER};")
        nb_lay = QHBoxLayout(navbar)
        nb_lay.setContentsMargins(0, 0, 0, 0)
        nb_lay.setSpacing(0)

        nav_items = [
("⏱", "Timer"), ("⚔", "Challenges"),
            ("💎", "Runes"), ("⚙", "Params"), ("📊", "Détails"),
        ]
        self._nav_btns = []
        for i, (icon, label) in enumerate(nav_items):
            btn = NavButton(icon, label)
            btn.clicked.connect(lambda _, idx=i: self._switch_tab(idx))
            nb_lay.addWidget(btn)
            self._nav_btns.append(btn)

        main_lay.addWidget(navbar)
        self._stack.setCurrentIndex(0)
        for i, btn in enumerate(self._nav_btns):
            btn.setChecked(i == 0)
        self._adjust_height(0)

    def _switch_tab(self, idx: int):
        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_btns):
            btn.setChecked(i == idx)
        self._adjust_height(idx)

    def _adjust_height(self, idx: int = 0):
        from PySide6.QtWidgets import QApplication
        self.setFixedWidth(self.WIDTH)
        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)
        # QStackedWidget expose uniquement le widget actif → sizeHint() est correct
        QApplication.processEvents()
        # Deux passes : la première déclenche le layout, la seconde mesure
        self.adjustSize()
        QApplication.processEvents()
        h = max(self.sizeHint().height(), 200)
        self.setFixedHeight(min(h, 900))

    # ── Stats ─────────────────────────────────────────────

    def _refresh_stats(self):
        all_kills, all_rares = [], []
        for md in self.maps.values():
            for gd in md['groups'].values():
                all_kills.extend(gd.get('deaths', []))
                all_rares.extend(gd.get('bambouto_times', []))

        def fmt(times):
            if not times: return "—"
            avg = sum(times) / len(times)
            m, s = divmod(int(avg), 60)
            return f"moy {m:02d}:{s:02d} · {len(times)}×"

        timer_tab = self._tabs[0]
        timer_tab.update_stats(f"Kill  {fmt(all_kills)}", f"Rare  {fmt(all_rares)}")
        self._tabs[4].update_session_stats(self.maps)

    # ── Callbacks Timer ───────────────────────────────────

    def _on_kill(self, group_name: str, map_name: str):
        gd = self.maps[map_name]['groups'][group_name]
        model.record_kill(gd)
        self._save()

    def _on_bambouto(self, group_name: str, map_name: str):
        gd = self.maps[map_name]['groups'][group_name]
        model.record_bambouto(gd)
        self._save()

    def _on_reset_group(self, group_name: str, map_name: str):
        gd = self.maps[map_name]['groups'][group_name]
        model.reset_group(gd)
        self._save()

    def _on_add_map(self):
        if len(self.maps) >= model.MAX_MAPS:
            return
        name = f"Map {len(self.maps)+1}"
        self.maps[name] = model.new_map_data()
        self._tabs[0].add_map(name, self.maps[name])
        self._save()

    def _on_delete_map(self):
        if len(self.maps) <= 1:
            return
        name = self._tabs[0]._current_map
        if name in self.maps:
            del self.maps[name]
            self._tabs[0].remove_map(name)
            self._save()

    def _on_reset_all(self):
        for md in self.maps.values():
            for gd in md['groups'].values():
                model.clear_group(gd)
        self._save()

    def _on_clear_stats(self):
        for md in self.maps.values():
            for gd in md['groups'].values():
                gd['deaths'] = []
                gd['bambouto_times'] = []
        self._save()

    def _on_rename_map(self, old: str, new: str):
        if new not in self.maps and old in self.maps:
            # Renommer in-place pour garder la même référence dict
            self.maps[new] = self.maps.pop(old)
            self._tabs[0].rename_map(old, new)
            self._save()

    def _on_change_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Choisir le dossier", str(Path.home()))
        if folder:
            new_path = Path(folder) / 'dofus_timers.json'
            model.set_data_file_path(new_path)
            self.data_file = new_path
            self.maps = model.load_maps(new_path)
            self._tabs[3].update_path(str(new_path))


