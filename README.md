<div align="center">

<img src="retro_toolbox.ico" width="80" alt="Retro Toolbox icon">

# Retro Toolbox

**Outil de gestion multi-comptes pour Dofus Rétro**

[![Version](https://img.shields.io/badge/version-1.0.5-orange?style=flat-square)](https://retro-toolbox.fr)
[![Platform](https://img.shields.io/badge/platform-Windows-blue?style=flat-square)](https://retro-toolbox.fr)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](https://python.org)
[![License](https://img.shields.io/badge/license-Source%20Available-lightgrey?style=flat-square)](LICENSE)

[⬇ Télécharger](https://retro-toolbox.fr) · [🌐 Site web](https://retro-toolbox.fr) · [💬 Discord](https://discord.com/users/364695997588307969)

</div>

---

## Fonctionnalités

| Onglet | Description |
|--------|-------------|
| ⏱ **Timer** | Suivi de respawn multi-maps et multi-groupes avec alertes automatiques |
| ⚔ **Challenges** | Gestionnaire de sorts par classe (Cra, Enutrof, Pandawa) — clic pour griser, glisser pour réorganiser |
| 💎 **Runes** | Tableau de poids des runes et calculateur de puit de forgemagie |
| 📊 **Détails** | Statistiques de session : kills, rares, durée, moyennes |

## Prérequis

- Windows 10 / 11
- Python 3.10 ou supérieur

```
pip install PySide6 Pillow
```

## Lancement en développement

```bash
git clone https://github.com/ton-pseudo/retro-toolbox.git
cd retro-toolbox
pip install -r requirements.txt
python main.py
```

## Build (Nuitka)

```powershell
python -m nuitka --onefile --windows-disable-console --enable-plugin=pyside6 --nofollow-import-to=cv2 --nofollow-import-to=pyautogui --nofollow-import-to=pygame --include-data-dir=spells=spells --include-data-files=retro_toolbox.ico=retro_toolbox.ico --include-data-files=qt.conf=qt.conf --windows-icon-from-ico=retro_toolbox.ico --output-filename="Retro Toolbox.exe" main.py
```

## Structure du projet

```
retro_toolbox/
├── main.py                 # Point d'entrée
├── main_window.py          # Fenêtre principale et navigation
├── model.py                # Données et persistance JSON
├── theme.py                # Palette de couleurs et styles QSS
├── spell_data.py           # Données des sorts
├── updater.py              # Vérification des mises à jour
├── requirements.txt
├── qt.conf
├── tabs/
│   ├── timer_tab.py        # Onglet timer
│   ├── challenges_tab.py   # Onglet challenges économe
│   ├── runes_tab.py        # Onglet runes / puit
│   ├── settings_tab.py     # Onglet paramètres
│   └── about_tab.py        # Onglet détails / stats
└── spells/
    ├── cra/                # Images des sorts Cra
    ├── enu/                # Images des sorts Enutrof
    └── pan/                # Images des sorts Pandawa
```

## Faux positifs antivirus

Les exécutables compilés avec Nuitka / Python peuvent être signalés à tort comme suspects par certains antivirus. Retro Toolbox ne lit pas l'écran, n'accède pas à vos fichiers personnels et ne se connecte à aucun serveur tiers (hormis la vérification de mises à jour sur `retro-toolbox.fr`).

Si votre antivirus bloque le lancement, ajoutez une exception ou contactez-moi sur Discord.

---

## Licence

Ce projet est distribué sous licence **Source Available** — voir le fichier [LICENSE](LICENSE).

Le code source est librement consultable à des fins éducatives ou personnelles. Toute redistribution, modification ou utilisation commerciale est interdite sans autorisation explicite de l'auteur.

---

## Mentions légales

> **Retro Toolbox n'est pas affilié à Ankama Games.**
>
> Dofus, Dofus Rétro et tous les éléments graphiques associés sont la propriété exclusive d'**Ankama Games**. Les images de sorts incluses dans ce projet (`spells/`) sont extraites du jeu Dofus Rétro et restent la propriété intellectuelle d'Ankama Games. Elles sont utilisées à titre informatif, sans but commercial, dans le cadre d'un outil utilitaire destiné aux joueurs.
>
> Ce projet n'est pas approuvé, sponsorisé ni soutenu par Ankama Games.

---

<div align="center">
Fait avec ♥ par <strong>Steal</strong>
</div>
