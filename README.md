<div align="center">

<img src="retro_toolbox.png" width="80" alt="Retro Toolbox icon">

# Retro Toolbox

**Outil de gestion pour Dofus Rétro**

[![Version](https://img.shields.io/badge/version-1.1.2-orange?style=flat-square)](https://retro-toolbox.fr)
[![Platform](https://img.shields.io/badge/platform-Windows-blue?style=flat-square)](https://retro-toolbox.fr)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](https://python.org)
[![License](https://img.shields.io/badge/license-Source%20Available-lightgrey?style=flat-square)](LICENSE)

[⬇ Télécharger](https://retro-toolbox.fr) · [🌐 Site web](https://retro-toolbox.fr) · [💬 Discord](https://discord.com/invite/Md8RJXdtQZ)

</div>

---

## Fonctionnalités

| Onglet | Description |
|--------|-------------|
| 👥 **Comptes** | Gestion multi-comptes — détection fenêtres Dofus, autofocus notifications, raccourcis globaux, profils d'ordre |
| 👤 **Dashboard** | Vue de tous vos personnages — classe, niveau, serveur, kamas, stuff complet et notes |
| 💎 **Runes** | Tableau de poids des runes, calculateur de puit détachable et compteur de tentatives exo PA/PM |
| 📝 **Todo** | Journal d'objectifs avec mise en forme — gras, couleurs, tailles, cases à cocher |
| ⏱ **Timer** | Suivi de respawn multi-maps et multi-groupes avec alertes automatiques |
| ⚔ **Challenges** | Gestionnaire de sorts par classe — clic pour griser, glisser pour réorganiser |
| 🎯 **Dots** | Overlay transparent — marquez des positions sur votre écran via raccourci clavier |
| 🔧 **Craft** | Calculateur de craft — coût des ressources, prix hôtel de vente, marge. Détection automatique du nom de ressource via clic droit sur Dofus |
| ⚙ **Paramètres** | Dossier de données, seuil d'alerte timer en minutes, thème clair/sombre |
| 📊 **Détails** | Statistiques de session : kills, rares, durée, moyennes |

### Onglet Comptes — détail

- **Détection automatique** des fenêtres Dofus ouvertes (polling toutes les 3s)
- **Autofocus** sur notifications Toast Windows : combat, échange, groupe, MP, défi, craft, PvP
- **Raccourcis globaux** configurables : suivant/précédent/principal/retour/Ctrl+Shift simulé
- **Mode Farm** : désactive l'autofocus combat d'un clic
- **Mode Déplacement** : clic gauche sur Dofus = personnage suivant automatiquement
- **Mode Farm Sadi** : ignore N tours de combat pour les Sadidas désignés
- **Profils d'ordre** : sauvegardez et appliquez des configurations prédéfinies (ex: "Farm Arakne")
- **Indicateur de tour actif** : surbrillance verte du personnage dont c'est le tour
- **Raccourcir les titres** de fenêtre dans la barre des tâches
- **Maximiser à l'ouverture** automatique des fenêtres Dofus

### Onglet Craft — détail

| Feature | Description |
|---------|-------------|
| 📦 **Gestion crafts** | Créez autant de crafts que souhaité avec un nom d'item et jusqu'à 8 ressources |
| 🧮 **Calcul automatique** | Coût total calculé en temps réel à partir des quantités et prix unitaires |
| 📊 **Comparaison prix** | Saisissez le prix hôtel de vente — la marge s'affiche en vert (bénéfice) ou rouge (perte) |
| 💰 **Formatage kamas** | Les prix sont formatés avec espaces automatiquement (10 000, 1 000 000) |
| 🖱 **OCR clic droit** | Clic droit sur une ressource dans Dofus — le nom est reconnu et rempli automatiquement |
| 💾 **Sauvegarde** | Tous vos crafts sont sauvegardés et restaurés à chaque ouverture |

### Onglet Runes — détail

| Feature | Description |
|---------|-------------|
| 📋 **Tableau de poids** | Poids Simple, Pa, Ra et Unité pour toutes les statistiques du jeu |
| 🧮 **Calculateur de puit** | Calculez le puit restant après chaque tentative — inline ou fenêtre détachable |
| ⚡ **Compteur exo PA/PM** | Boutons + / − et reset pour suivre vos tentatives, valeur sauvegardée entre les sessions |

---

## Prérequis

- Windows 10 / 11
- Python 3.10 ou supérieur

```
pip install PySide6 pywin32 keyboard psutil winsdk pillow pytesseract
```

> **Notifications Toast** (autofocus) : `winsdk` nécessite les **Visual Studio Build Tools 2022**.
> Téléchargement gratuit : [Visual Studio Build Tools](https://aka.ms/vs/17/release/vs_BuildTools.exe)
> Cocher "Développement Desktop en C++" lors de l'installation.

> **Détection OCR clic droit** (onglet Craft) : nécessite **Tesseract OCR** installé séparément.
> Téléchargement gratuit : [Tesseract for Windows](https://github.com/UB-Mannheim/tesseract/wiki)
> Installer dans `C:\Program Files\Tesseract-OCR\` (chemin détecté automatiquement).

> Si l'application ne se lance pas, installe également :
> **[Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)** (Microsoft, gratuit)

---

## Lancement en développement

```bash
git clone https://github.com/Webn-Benjamin/retro_toolbox.git
cd retro_toolbox
pip install -r requirements.txt
python main.py
```

---

## Build (PyInstaller)

```powershell
python -m PyInstaller --onefile --windowed --icon=retro_toolbox.ico --add-data "pictures;pictures" --add-data "retro_toolbox.ico;." --add-data "qt.conf;." --name "Retro Toolbox" main.py
```

L'exécutable est généré dans le dossier `dist/`.

---

## Structure du projet

```
retro_toolbox/
├── main.py                    # Point d'entrée
├── main_window.py             # Fenêtre principale et navigation
├── model.py                   # Données et persistance JSON
├── theme.py                   # Palette de couleurs et styles QSS
├── spell_data.py              # Données des sorts
├── updater.py                 # Vérification et installation des mises à jour
├── requirements.txt
├── qt.conf
├── tabs/
│   ├── accounts_tab.py        # Onglet comptes / multi-compte
│   ├── dashboard_tab.py       # Onglet dashboard personnages
│   ├── timer_tab.py           # Onglet timer
│   ├── challenges_tab.py      # Onglet challenges économe
│   ├── runes_tab.py           # Onglet runes / puit / compteur exo
│   ├── todo_tab.py            # Onglet todo list
│   ├── overlay_tab.py         # Onglet dots / overlay
│   ├── settings_tab.py        # Onglet paramètres
│   ├── craft_tab.py           # Onglet craft / calculateur / OCR clic droit
│   ├── about_tab.py           # Onglet détails / stats
│   └── accounts/
│       ├── window_manager.py  # Détection fenêtres Dofus (Win32)
│       ├── toast_reader.py    # Lecture notifications Toast (winsdk)
│       ├── hotkey_manager.py  # Raccourcis globaux + Ctrl+Shift
│       ├── move_mode.py       # Mode déplacement (hook souris)
│       ├── characters_panel.py
│       ├── shortcuts_panel.py
│       ├── settings_panel.py
│       └── notif_help.py      # Tutoriel notifications
└── pictures/
    └── classes/               # Images des classes Dofus Rétro
```

---

## Faux positifs antivirus

Les exécutables compilés avec PyInstaller peuvent être signalés à tort par certains antivirus. Retro Toolbox ne lit pas l'écran en permanence, n'accède pas à vos fichiers personnels et ne se connecte à aucun serveur tiers (hormis la vérification de mises à jour sur `retro-toolbox.fr`).

La fonctionnalité OCR (onglet Craft) effectue un screenshot localement uniquement lors d'un clic droit sur Dofus, quand l'onglet Craft est actif.

Si votre antivirus bloque le lancement, ajoutez une exception ou contactez-nous sur [Discord](https://discord.com/invite/Md8RJXdtQZ).

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
