"""settings_panel.py — Paramètres du module multi-comptes."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt
from typing import Callable
import theme as T
from tabs.accounts.sadi_manager import SadiManager


def _lbl(txt, color=None, sz="8.5pt", bold=False, italic=False):
    l = QLabel(txt)
    ss = f"background:transparent;font-size:{sz};"
    if color:  ss += f"color:{color};"
    if bold:   ss += "font-weight:bold;"
    if italic: ss += "font-style:italic;"
    l.setStyleSheet(ss)
    return l


class _Toggle(QFrame):
    """Ligne paramètre avec switch ON/OFF."""

    def __init__(self, key: str, label: str, checked: bool,
                 on_change: Callable[[bool], None] | None = None):
        super().__init__()
        self._key    = key
        self._value  = checked
        self._cb     = on_change
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)
        self.setStyleSheet(
            f"QFrame{{background:transparent;border-bottom:1px solid {T.BORDER};}}"
            f"QFrame:hover{{background:{T.SURFACE2};}}")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(10)

        self._lbl = QLabel(label)
        self._lbl.setStyleSheet(
            f"background:transparent;color:{T.TEXT};font-size:8.5pt;")
        lay.addWidget(self._lbl, 1)

        self._sw = QLabel()
        self._sw.setFixedWidth(54)
        self._sw.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sw.setStyleSheet("font-size:9pt;font-weight:bold;padding:2px;")
        lay.addWidget(self._sw)

        self._refresh()
        for w in (self, self._lbl, self._sw):
            w.mousePressEvent = lambda e: self._flip()

    def _refresh(self):
        if self._value:
            self._sw.setText("ON  ●")
            self._sw.setStyleSheet(
                f"background:{T.GREEN};color:white;"
                f"font-size:9pt;font-weight:bold;padding:2px;")
        else:
            self._sw.setText("●  OFF")
            self._sw.setStyleSheet(
                f"background:{T.BG_DARK};color:{T.HINT};"
                f"font-size:9pt;font-weight:bold;padding:2px;")

    def _flip(self):
        self._value = not self._value
        self._refresh()
        if self._cb:
            self._cb(self._value)

    @property
    def value(self) -> bool:
        return self._value


class SettingsPanel(QWidget):

    def __init__(self, cfg: dict, on_save, parent=None):
        super().__init__(parent)
        self._cfg    = cfg
        self._on_save = on_save
        self._toggles: dict[str, _Toggle] = {}
        # Mode Farm Sadi
        sadi_cfg   = self._cfg.get("sadi", {})
        self.sadi  = SadiManager(turns=sadi_cfg.get("turns", 3))
        self.sadi.set_sadis(set(sadi_cfg.get("sadis", [])))
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet(
            f"background:{T.BG_DARK};border-bottom:1px solid {T.BORDER};")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(10, 6, 10, 6)
        hl.addWidget(_lbl("Paramètres", T.TEXT, "9pt", bold=True))
        outer.addWidget(hdr)

        # Scroll
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sc.setStyleSheet(
            f"QScrollArea{{background:{T.BG};border:none;}}"
            f"QScrollBar:vertical{{background:{T.BG_DARK};width:4px;}}"
            f"QScrollBar::handle:vertical{{background:{T.BORDER2};min-height:20px;}}"
            f"QScrollBar::handle:vertical:hover{{background:{T.ORANGE};}}"
            f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        inner = QWidget(); inner.setStyleSheet(f"background:{T.BG};")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(0, 0, 0, 10)
        lay.setSpacing(0)
        sc.setWidget(inner)
        outer.addWidget(sc)

        s = self._cfg.get("settings", {})

        # ── Autofocus ──────────────────────────────────────
        lay.addWidget(self._section_header("⚡  Autofocus sur notification"))
        lay.addWidget(_lbl(
            "  Bascule automatiquement sur le personnage concerné.",
            T.HINT, "9pt", italic=True))
        _af_defaults = {
            "autofocus_combat":  True,
            "autofocus_echange": True,
            "autofocus_groupe":  True,
            "autofocus_mp":      True,
            "autofocus_defi":    True,
            "autofocus_craft":   True,
            "autofocus_pvp":     True,
        }
        for key, emoji, label in [
            ("autofocus_combat",  "⚔️", "Combat"),
            ("autofocus_echange", "🔄", "Échange"),
            ("autofocus_groupe",  "👥", "Groupe / Guilde"),
            ("autofocus_mp",      "💬", "Message privé"),
            ("autofocus_defi",    "🏆", "Défi"),
            ("autofocus_craft",   "🔨", "Craft terminé"),
            ("autofocus_pvp",     "🛡️", "PvP / Percepteur"),
        ]:
            t = self._add_toggle(key, f"{emoji}  {label}", s.get(key, _af_defaults.get(key, False)))
            lay.addWidget(t)

        # ── Notifications ──────────────────────────────────
        lay.addWidget(self._section_header("🔔  Notifications Toast"))
        lay.addWidget(self._add_toggle(
            "remove_notif_after_read",
            "🗑  Supprimer après lecture",
            s.get("remove_notif_after_read", True)))

        # ── Fenêtres ───────────────────────────────────────
        lay.addWidget(self._section_header("🗖  Fenêtres"))
        lay.addWidget(self._add_toggle(
            "maximize_on_launch",
            "🗖  Maximiser à l'ouverture",
            s.get("maximize_on_launch", False)))
        lay.addWidget(self._add_toggle(
            "shorten_titles",
            "📋  Raccourcir les titres",
            s.get("shorten_titles", False),
            on_change=self._on_shorten))

        # ── Ctrl+Shift ─────────────────────────────────────
        lay.addWidget(self._section_header("⇧  Ctrl+Shift"))
        lay.addWidget(self._add_toggle(
            "ctrlshift_autostart",
            "⇧  Activer au démarrage",
            s.get("ctrlshift_autostart", False)))

        lay.addStretch()

    def _section_header(self, title: str) -> QLabel:
        l = QLabel(f"  {title}")
        l.setStyleSheet(
            f"background:{T.BG_DARK};color:{T.HINT};"
            f"font-size:8pt;font-weight:bold;letter-spacing:1px;"
            f"padding:4px 0;border-top:1px solid {T.BORDER};"
            f"border-bottom:1px solid {T.BORDER};")
        l.setFixedHeight(24)
        return l

    def _add_toggle(self, key, label, checked, on_change=None) -> _Toggle:
        def _combined(v, k=key, cb=on_change):
            self._cfg.setdefault("settings", {})[k] = v
            self._on_save()
            if cb: cb(v)
        t = _Toggle(key, label, checked, _combined)
        self._toggles[key] = t
        return t

    def get(self, key: str, default=False) -> bool:
        t = self._toggles.get(key)
        return t.value if t else self._cfg.get("settings", {}).get(key, default)

    def refresh_sadi_rows(self, pseudos: list[str]):
        """Met à jour la liste des Sadidas avec les persos détectés."""
        while self._sadi_lay.count():
            item = self._sadi_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        saved = set(self._cfg.get("sadi", {}).get("sadis", []))
        for pseudo in pseudos:
            row = _Toggle(
                key=f"sadi_{pseudo}",
                label=f"🌿  {pseudo}",
                checked=(pseudo in saved))
            def _cb(v, p=pseudo):
                sadis = set(self._cfg.get("sadi", {}).get("sadis", []))
                if v: sadis.add(p)
                else: sadis.discard(p)
                self._cfg.setdefault("sadi", {})["sadis"] = list(sadis)
                self.sadi.set_sadis(sadis)
                self._on_save()
            row._cb = _cb
            self._sadi_lay.addWidget(row)
        if not pseudos:
            self._sadi_lay.addWidget(
                _lbl("Aucun personnage détecté", T.HINT, "9.5pt", italic=True))

    def _change_turns(self, delta: int):
        current = int(self._turns_lbl.text())
        new = max(1, min(10, current + delta))
        self._turns_lbl.setText(str(new))
        self._cfg.setdefault("sadi", {})["turns"] = new
        self.sadi.turns = new
        self._on_save()

    def _on_shorten(self, enabled: bool):
        try:
            from tabs.accounts.window_manager import apply_short_titles
            apply_short_titles(enabled)
        except Exception: pass
