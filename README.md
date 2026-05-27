<div align="center">

<img src="retro_toolbox.ico" width="80" alt="Retro Toolbox icon">

# Retro Toolbox

**Outil de gestion pour Dofus Rétro**

[![Version](https://img.shields.io/badge/version-1.0.7-orange?style=flat-square)](https://retro-toolbox.fr)
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
| 💎 **Runes** | Tableau de poids des runes et calculateur de puit de forgemagie détachable |
| 📝 **Todo** | Journal d'objectifs avec mise en forme — gras, couleurs, tailles de police |
| ⚙ **Paramètres** | Dossier de données et seuil d'alerte timer |
| 📊 **Détails** | Statistiques de session : kills, rares, durée, moyennes |

## Prérequis

- Windows 10 / 11
- Python 3.10 ou supérieur

```
pip install PySide6 Pillow
```

> Si l'application ne se lance pas, installe également :
> **[Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)** (Microsoft, gratuit)

## Lancement en développement

```bash
git clone https://github.com/Webn-Benjamin/retro_toolbox.git
cd retro_toolbox
pip install -r requirements.txt
python main.py
```

## Build (PyInstaller)

```powershell
python -m PyInstaller --onefile --windowed --add-data "spells;spells" --add-data "retro_toolbox.ico;." --add-data "qt.conf;." --name "Retro Toolbox" main.py
```

L'exécutable est généré dans le dossier `dist/`.

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
│   ├── todo_tab.py         # Onglet todo list
│   ├── settings_tab.py     # Onglet paramètres
│   └── about_tab.py        # Onglet détails / stats
└── spells/
    ├── cra/                # Images des sorts Cra
    ├── enu/                # Images des sorts Enutrof
    └── pan/                # Images des sorts Pandawa
```

## Faux positifs antivirus

Les exécutables compilés avec PyInstaller / Python peuvent être signalés à tort comme suspects par certains antivirus. Retro Toolbox ne lit pas l'écran, n'accède pas à vos fichiers personnels et ne se connecte à aucun serveur tiers (hormis la vérification de mises à jour sur `retro-toolbox.fr`).

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