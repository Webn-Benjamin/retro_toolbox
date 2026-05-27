"""
main_window.py — Fenêtre principale PySide6 de Retro Toolbox.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QFileDialog, QSizePolicy, QStackedWidget
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QIcon
from pathlib import Path

import model, theme


class _FitStack(QStackedWidget):
    """QStackedWidget qui expose uniquement la taille du widget actif."""
    def sizeHint(self):
        w = self.currentWidget()
        return w.sizeHint() if w else super().sizeHint()

    def minimumSizeHint(self):
        w = self.currentWidget()
        return w.minimumSizeHint() if w else super().minimumSizeHint()
from tabs.timer_tab      import TimerTab
from tabs.challenges_tab import ChallengesTab
from tabs.runes_tab      import RunesTab
from tabs.settings_tab   import SettingsTab
from tabs.about_tab      import AboutTab
from tabs.todo_tab       import TodoTab


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


class WelcomeDialog(QWidget):
    """Fenêtre de bienvenue affichée au premier lancement."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("Retro Toolbox — Premier lancement")
        self.setFixedWidth(400)
        self._chosen_folder = None
        import sys
        def _res(rel):
            if getattr(sys, 'frozen', False):
                return str(Path(sys._MEIPASS) / rel)
            return str(Path(__file__).parent / rel)
        from PySide6.QtGui import QIcon
        self.setWindowIcon(QIcon(_res("retro_toolbox.ico")))
        self.setStyleSheet(f"""
            QWidget {{ background:{theme.BG}; color:{theme.TEXT};
                       font-family:'Segoe UI'; }}
            QFrame#card {{ background:{theme.SURFACE};
                           border:1px solid {theme.BORDER};
                           border-radius:6px; }}
        """)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 28, 24, 24)
        lay.setSpacing(16)

        # Logo + titre
        title = QLabel("🎮 Retro Toolbox")
        title.setStyleSheet(
            f"font-size:20pt;font-weight:bold;color:{theme.TEXT};"
            f"background:transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        sub = QLabel("Premier lancement — Configuration")
        sub.setStyleSheet(
            f"font-size:10pt;color:{theme.HINT};background:transparent;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sub)

        # Séparateur
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{theme.BORDER};")
        lay.addWidget(sep)

        # Explication
        card = QFrame(); card.setObjectName("card")
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(16, 14, 16, 14)
        card_lay.setSpacing(10)

        info = QLabel(
            "Retro Toolbox a besoin d'un dossier pour sauvegarder "
            "tes timers, statistiques et préférences.")
        info.setWordWrap(True)
        info.setStyleSheet(f"color:{theme.TEXT};font-size:10pt;background:transparent;")
        card_lay.addWidget(info)

        steps = QLabel(
            "① Clique sur <b>Choisir un dossier</b><br>"
            "② Sélectionne ou crée un dossier sur ton Bureau ou tes Documents<br>"
            "③ Retro Toolbox y créera automatiquement son fichier de données")
        steps.setWordWrap(True)
        steps.setStyleSheet(
            f"color:{theme.SUBTEXT};font-size:9pt;line-height:1.6;"
            f"background:transparent;")
        steps.setTextFormat(Qt.TextFormat.RichText)
        card_lay.addWidget(steps)

        lay.addWidget(card)

        # Dossier sélectionné
        self._folder_lbl = QLabel("Aucun dossier sélectionné")
        self._folder_lbl.setWordWrap(True)
        self._folder_lbl.setStyleSheet(
            f"color:{theme.HINT};font-size:8pt;background:transparent;"
            f"font-style:italic;")
        self._folder_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._folder_lbl)

        # Boutons
        btn_choose = QPushButton("📁  Choisir un dossier")
        btn_choose.setStyleSheet(f"""
            QPushButton {{
                background:{theme.BG_DARK};color:{theme.TEXT};
                border:1px solid {theme.BORDER};border-radius:4px;
                padding:10px 20px;font-size:10pt;font-weight:bold;
            }}
            QPushButton:hover {{
                border-color:{theme.ORANGE};color:{theme.ORANGE};
            }}
        """)
        btn_choose.clicked.connect(self._choose_folder)
        lay.addWidget(btn_choose)

        self._btn_start = QPushButton("✔  Démarrer Retro Toolbox")
        self._btn_start.setEnabled(False)
        self._btn_start.setStyleSheet(f"""
            QPushButton {{
                background:{theme.ORANGE};color:white;
                border:none;border-radius:4px;
                padding:12px 20px;font-size:11pt;font-weight:bold;
            }}
            QPushButton:hover {{ background:{theme.ORANGE_L}; }}
            QPushButton:disabled {{
                background:{theme.BG_DARK};color:{theme.HINT};
            }}
        """)
        self._btn_start.clicked.connect(self._confirm)
        lay.addWidget(self._btn_start)

        note = QLabel("💡 Tu pourras changer ce dossier plus tard dans Paramètres.")
        note.setWordWrap(True)
        note.setStyleSheet(f"color:{theme.HINT};font-size:8pt;background:transparent;")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(note)

        self.adjustSize()

    def _choose_folder(self):
        from PySide6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(
            self, "Choisir le dossier de données", str(Path.home()))
        if folder:
            self._chosen_folder = folder
            # Afficher le chemin de façon courte
            short = folder if len(folder) < 45 else "..." + folder[-42:]
            self._folder_lbl.setText(f"📁 {short}")
            self._folder_lbl.setStyleSheet(
                f"color:{theme.ORANGE};font-size:8pt;"
                f"background:transparent;font-style:normal;")
            self._btn_start.setEnabled(True)

    def _confirm(self):
        if self._chosen_folder:
            self.close()

    def get_folder(self):
        return self._chosen_folder


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
        # Afficher la belle fenêtre de bienvenue
        dlg = WelcomeDialog()
        dlg.show()
        from PySide6.QtWidgets import QApplication
        # Attendre que l'utilisateur choisisse
        while dlg.isVisible():
            QApplication.processEvents()
        folder = dlg.get_folder() or str(Path.home())
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
            TimerTab(self.maps, callbacks),   # 0
            ChallengesTab(),                  # 1
            RunesTab(),                       # 2
            TodoTab(),                        # 3
            SettingsTab(str(self.data_file), self._on_change_folder),  # 4
            AboutTab(),                       # 5
        ]

        # Stack — QStackedWidget expose uniquement le widget actif pour sizeHint
        self._stack = _FitStack()
        self._stack.setContentsMargins(0, 0, 0, 0)
        self._stack.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        for tab in self._tabs:
            tab.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
            self._stack.addWidget(tab)
        main_lay.addWidget(self._stack)

        # Navbar bas
        navbar = QWidget()
        navbar.setObjectName("navbar")
        navbar.setFixedHeight(60)
        navbar.setStyleSheet(f"background:{theme.BG_DARK};border-top:1px solid {theme.BORDER};")
        nb_lay = QHBoxLayout(navbar)
        nb_lay.setContentsMargins(0, 0, 0, 0)
        nb_lay.setSpacing(0)

        nav_items = [
            ("⏱", "Timer"), ("⚔", "Challenges"), ("💎", "Runes"), ("📝", "Todo"),
        ]
        self._nav_btns = []
        for i, (icon, label) in enumerate(nav_items):
            btn = NavButton(icon, label)
            btn.clicked.connect(lambda _, idx=i: self._switch_tab(idx))
            nb_lay.addWidget(btn)
            self._nav_btns.append(btn)

        # Bouton ⋯ pour les onglets secondaires
        self._more_btn = NavButton("⋯", "Plus")
        self._more_btn.clicked.connect(self._toggle_more_menu)
        nb_lay.addWidget(self._more_btn)
        self._nav_btns.append(self._more_btn)

        main_lay.addWidget(navbar)
        self._stack.setCurrentIndex(0)
        for i, btn in enumerate(self._nav_btns):
            btn.setChecked(i == 0)

        # Menu popup pour onglets secondaires
        self._more_menu = QFrame(self)
        self._more_menu.setObjectName("more_menu")
        self._more_menu.setWindowFlags(Qt.WindowType.Popup)
        self._more_menu.setStyleSheet(
            f"QFrame#more_menu{{background:{theme.SURFACE};border:1px solid {theme.BORDER};"
            f"border-radius:4px;}}")
        mm_lay = QVBoxLayout(self._more_menu)
        mm_lay.setContentsMargins(6, 6, 6, 6); mm_lay.setSpacing(4)

        for idx, (icon, label) in [(4, ("⚙", "Paramètres")), (5, ("📊", "Détails"))]:
            btn = QPushButton(f"{icon}  {label}")
            btn.setStyleSheet(
                f"QPushButton{{background:transparent;color:{theme.TEXT};"
                f"border:none;border-radius:3px;padding:8px 14px;"
                f"text-align:left;font-size:10pt;}}"
                f"QPushButton:hover{{background:{theme.BG_DARK};color:{theme.ORANGE};}}")
            btn.clicked.connect(lambda _, i=idx: (self._more_menu.hide(), self._switch_tab(i)))
            mm_lay.addWidget(btn)
        self._more_menu.adjustSize()
        self._more_menu.hide()

        self._adjust_height(0)

    def _toggle_more_menu(self):
        if self._more_menu.isVisible():
            self._more_menu.hide()
            return
        # Positionner au-dessus du bouton ⋯
        btn = self._more_btn
        pos = btn.mapToGlobal(btn.rect().topLeft())
        self._more_menu.adjustSize()
        pos.setY(pos.y() - self._more_menu.height() - 4)
        pos.setX(pos.x() - self._more_menu.width() + btn.width())
        self._more_menu.move(pos)
        self._more_menu.show()
        self._more_menu.raise_()

    def _switch_tab(self, idx: int):
        self.setUpdatesEnabled(False)
        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_btns):
            btn.setChecked(i == idx)
        self._adjust_height(idx)
        self.setUpdatesEnabled(True)

    def _adjust_height(self, idx: int = 0):
        from PySide6.QtWidgets import QApplication
        self.setFixedWidth(self.WIDTH)
        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)
        # Propager updateGeometry depuis le tab actif jusqu'à la fenêtre
        current = self._stack.currentWidget()
        if current:
            w = current
            while w:
                w.updateGeometry()
                w = w.parentWidget()
        self.adjustSize()

    # ── Stats ─────────────────────────────────────────────

    def _refresh_stats(self):
        # Stats de la map active uniquement
        timer_tab = self._tabs[0]
        current_map = getattr(timer_tab, '_current_map', None)
        all_kills, all_rares = [], []
        maps_to_scan = {}
        if current_map and current_map in self.maps:
            maps_to_scan = {current_map: self.maps[current_map]}
        else:
            maps_to_scan = self.maps

        for md in maps_to_scan.values():
            for gd in md['groups'].values():
                all_kills.extend(gd.get('deaths', []))
                all_rares.extend(gd.get('bambouto_times', []))

        def fmt(times):
            if not times: return "—"
            avg = sum(times) / len(times)
            m, s = divmod(int(avg), 60)
            return f"moy {m:02d}:{s:02d} · {len(times)}×"

        timer_tab.update_stats(f"Kill  {fmt(all_kills)}", f"Rare  {fmt(all_rares)}")
        self._tabs[5].update_session_stats(self.maps)

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
            self._tabs[4].update_path(str(new_path))


