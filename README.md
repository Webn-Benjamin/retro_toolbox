# Retro Toolbox — PySide6

## Installation

```bash
pip install PySide6 Pillow
```

## Lancement

```bash
python main.py
```

## Build .exe avec Nuitka (recommandé)

```bash
pip install nuitka
python -m nuitka --onefile --windows-disable-console ^
  --enable-plugin=pyside6 ^
  --nofollow-import-to=cv2 ^
  --nofollow-import-to=pyautogui ^
  --nofollow-import-to=pygame ^
  --include-data-dir=spells=spells ^
  --include-data-files=retro_toolbox.ico=retro_toolbox.ico ^
  --include-data-files=qt.conf=qt.conf ^
  --windows-icon-from-ico=retro_toolbox.ico ^
  --output-filename="Retro Toolbox.exe" ^
  main.py
```

## Structure

```
retro_toolbox_qt/
├── main.py              # Point d'entrée
├── main_window.py       # Fenêtre principale
├── theme.py             # Palette + QSS
├── model.py             # Données
├── spell_data.py        # Données sorts
├── updater.py           # Mises à jour
├── qt.conf              # Fix DPI Windows
├── requirements.txt
├── tabs/
│   ├── timer_tab.py
│   ├── challenges_tab.py
│   ├── runes_tab.py
│   ├── settings_tab.py
│   └── about_tab.py
└── spells/
    ├── cra/   9-1.png … 9-22.png + 99-23.png … 99-30.png
    ├── enu/   3-1.png … 3-22.png + 99-23.png … 99-30.png
    └── pan/   12-1.png … 12-22.png + 99-23.png … 99-30.png
```

## Dépendances
- PySide6 — interface graphique
- Pillow — traitement des images de sorts
