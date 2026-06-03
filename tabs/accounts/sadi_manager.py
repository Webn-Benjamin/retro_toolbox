"""sadi_manager.py — Mode Farm Sadi : ignore N tours de combat pour les Sadidas."""
from __future__ import annotations


class SadiManager:
    """
    Compteur de tours par personnage Sadida.

    Utilisation :
        mgr = SadiManager(turns=3)
        mgr.set_sadis({"St-Sadi", "Perso2"})

        # Quand on active le mode pour un perso :
        mgr.activate("St-Sadi")

        # À chaque notification de combat :
        skip, remaining = mgr.check_combat("St-Sadi")
        if skip:
            # Ne pas basculer sur ce perso ce tour
    """

    def __init__(self, turns: int = 3):
        self._sadis:    set[str]       = set()
        self._counters: dict[str, int] = {}
        self._turns: int = max(1, turns)

    # ── Propriétés ────────────────────────────────────────

    @property
    def turns(self) -> int:
        return self._turns

    @turns.setter
    def turns(self, value: int):
        self._turns = max(1, int(value))

    @property
    def sadis(self) -> set[str]:
        return set(self._sadis)

    # ── Config ────────────────────────────────────────────

    def set_sadis(self, pseudos: set[str]):
        """Met à jour la liste des Sadidas. Annule les compteurs retirés."""
        self._sadis = set(pseudos)
        for p in list(self._counters):
            if p not in self._sadis:
                del self._counters[p]

    def is_sadi(self, pseudo: str) -> bool:
        return pseudo in self._sadis

    # ── Contrôle ──────────────────────────────────────────

    def activate(self, pseudo: str):
        """Active (ou réinitialise) le compteur pour ce Sadida."""
        if pseudo in self._sadis:
            self._counters[pseudo] = self._turns

    def check_combat(self, pseudo: str) -> tuple[bool, int]:
        """
        À appeler à chaque notification de combat pour ce perso.
        Retourne (True, tours_restants) si le tour doit être ignoré.
        Retourne (False, 0) sinon.
        Décrémente le compteur à chaque appel positif.
        """
        remaining = self._counters.get(pseudo, 0)
        if remaining <= 0:
            return False, 0
        new = remaining - 1
        if new == 0:
            del self._counters[pseudo]
        else:
            self._counters[pseudo] = new
        return True, new

    def remaining(self, pseudo: str) -> int:
        """Nombre de tours restants pour ce perso (0 = inactif)."""
        return self._counters.get(pseudo, 0)

    def cancel(self, pseudo: str):
        self._counters.pop(pseudo, None)

    def cancel_all(self):
        self._counters.clear()

    def is_active(self, pseudo: str) -> bool:
        return self._counters.get(pseudo, 0) > 0

    def any_active(self) -> bool:
        return bool(self._counters)
