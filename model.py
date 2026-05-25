"""
model.py — Données, sauvegarde et logique métier.
Aucune dépendance tkinter.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path


# ──────────────────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────────────────

CONFIG_FILE  = Path.home() / '.dofus_timer_config.json'
DEFAULT_GROUPS = ['Groupe 1', 'Groupe 2', 'Groupe 3']
MAX_MAPS = 4


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

def new_group_data() -> dict:
    return {
        'deaths':         [],
        'last_death':     None,
        'bambouto_times': [],
        'last_bambouto':  None,
        'position':       {'v': None, 'h': None},  # v: Haut/Milieu/Bas  h: Gauche/Milieu/Droite
    }


def new_map_data() -> dict:
    return {
        'coord_x': 0,
        'coord_y': 0,
        'groups':  {name: new_group_data() for name in DEFAULT_GROUPS},
    }


# ──────────────────────────────────────────────────────────
# Config (chemin du fichier de données + géométrie fenêtre)
# ──────────────────────────────────────────────────────────

def load_config() -> dict:
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_config(updates: dict) -> None:
    config = load_config()
    config.update(updates)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_data_file_path() -> Path | None:
    """Retourne le chemin sauvegardé s'il est valide, sinon None."""
    cfg = load_config()
    saved = cfg.get('data_file_path')
    if saved and Path(saved).parent.exists():
        return Path(saved)
    return None


def set_data_file_path(path: Path) -> None:
    save_config({'data_file_path': str(path)})


def get_window_geometry() -> str | None:
    return load_config().get('window_geometry')


def set_window_geometry(geo: str) -> None:
    save_config({'window_geometry': geo})


def get_alert_threshold() -> int:
    return int(load_config().get('alert_threshold_sec', 600))


def set_alert_threshold(seconds: int) -> None:
    save_config({'alert_threshold_sec': seconds})


# ──────────────────────────────────────────────────────────
# Persistance des maps
# ──────────────────────────────────────────────────────────

def _write_default_maps(data_file: Path, maps: dict) -> None:
    """Ecrit les maps par défaut dans un nouveau fichier JSON."""
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    for map_name, map_data in maps.items():
        data[map_name] = {'_coord_x': 0, '_coord_y': 0}
        for gn in map_data['groups']:
            data[map_name][gn] = {
                'deaths': [], 'last_death': None,
                'bambouto_times': [], 'last_bambouto': None,
                'position': {'v': None, 'h': None},
            }
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_maps(data_file: Path) -> dict:
    # Crée le fichier avec une map par défaut s'il n'existe pas
    if not data_file.exists():
        default = {'Map 1': new_map_data()}
        _write_default_maps(data_file, default)
        return default

    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        # Fichier corrompu : repart de zéro
        default = {'Map 1': new_map_data()}
        _write_default_maps(data_file, default)
        return default

    maps = {}
    for map_name, map_data in data.items():
        maps[map_name] = {
            'coord_x': map_data.get('_coord_x', 0),
            'coord_y': map_data.get('_coord_y', 0),
            'groups':  {},
        }
        for gn, gd in map_data.items():
            if gn.startswith('_'):
                continue
            maps[map_name]['groups'][gn] = {
                'deaths':         gd.get('deaths', []),
                'last_death':     datetime.fromisoformat(gd['last_death'])
                                  if gd.get('last_death') else None,
                'bambouto_times': gd.get('bambouto_times', []),
                'last_bambouto':  datetime.fromisoformat(gd['last_bambouto'])
                                  if gd.get('last_bambouto') else None,
                'position':       _load_position(gd.get('position')),
            }
    return maps


def _load_position(raw) -> dict:
    """Compatibilité ascendante : ancien format string -> nouveau dict."""
    if isinstance(raw, dict):
        return {'v': raw.get('v'), 'h': raw.get('h')}
    return {'v': None, 'h': None}


def save_maps(maps: dict, data_file: Path) -> None:
    data = {}
    for map_name, map_data in maps.items():
        data[map_name] = {
            '_coord_x': map_data.get('coord_x', 0),
            '_coord_y': map_data.get('coord_y', 0),
        }
        for gn, gd in map_data['groups'].items():
            data[map_name][gn] = {
                'deaths':         gd['deaths'],
                'last_death':     gd['last_death'].isoformat()
                                  if gd['last_death'] else None,
                'bambouto_times': gd['bambouto_times'],
                'last_bambouto':  gd['last_bambouto'].isoformat()
                                  if gd['last_bambouto'] else None,
                'position':       gd.get('position'),
            }
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def default_maps() -> dict:
    return {f"Map {i}": new_map_data() for i in range(1, 4)}


# ──────────────────────────────────────────────────────────
# Logique métier (timers, stats)
# ──────────────────────────────────────────────────────────

def record_kill(group_data: dict) -> None:
    now = datetime.now()
    if group_data['last_death'] is not None:
        delta = (now - group_data['last_death']).total_seconds()
        group_data['deaths'].append(delta)
    group_data['last_death'] = now


def record_bambouto(group_data: dict) -> None:
    now = datetime.now()
    # Delta depuis le dernier événement (kill OU rare), pas seulement rare
    lk = group_data['last_death']
    lb = group_data['last_bambouto']
    last_event = (max(lk, lb) if lk and lb else lk or lb or None)
    if last_event is not None:
        group_data['bambouto_times'].append((now - last_event).total_seconds())
    group_data['last_bambouto'] = now


def reset_group(group_data: dict) -> None:
    group_data['last_death']   = None
    group_data['last_bambouto'] = None


def clear_group(group_data: dict) -> None:
    group_data['deaths']        = []
    group_data['last_death']    = None
    group_data['bambouto_times'] = []
    group_data['last_bambouto'] = None


def elapsed_seconds(group_data: dict) -> float | None:
    lk = group_data['last_death']
    lb = group_data['last_bambouto']
    last = (max(lk, lb) if lk and lb else lk or lb or None)
    if last is None:
        return None
    return (datetime.now() - last).total_seconds()


def format_elapsed(seconds: float | None) -> str:
    if seconds is None:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def compute_stats(times: list[float], label: str) -> str:
    if not times:
        return f"{label}   —"
    avg = sum(times) / len(times)
    am, as_ = divmod(int(avg), 60)
    lm, ls  = divmod(int(times[-1]), 60)
    return f"{label}   moy {am:02d}:{as_:02d}  ·  last {lm:02d}:{ls:02d}  ·  {len(times)}×"


def next_map_number(existing_names: list[str]) -> int:
    nums = []
    for name in existing_names:
        if name.startswith("Map "):
            try:
                nums.append(int(name[4:]))
            except ValueError:
                pass
    n = 1
    while n in nums:
        n += 1
    return n


def move_data_file(old: Path, new_folder: Path) -> Path:
    new_path = new_folder / 'dofus_timers.json'
    if old.exists():
        shutil.copy(old, new_path)
    return new_path


def rename_map(maps: dict, old_name: str, new_name: str) -> dict:
    # Renomme une map en preservant l'ordre et les donnees
    return {(new_name if k == old_name else k): v for k, v in maps.items()}


def rename_group(maps: dict, map_name: str, old_name: str, new_name: str) -> None:
    # Renomme un groupe dans une map (en place)
    groups = maps[map_name]['groups']
    maps[map_name]['groups'] = {
        (new_name if k == old_name else k): v for k, v in groups.items()
    }


# ──────────────────────────────────────────────────────────
# Persistance onglet Traque
# ──────────────────────────────────────────────────────────

def get_tracking_prefs() -> dict:
    cfg = load_config()
    return {
        'threshold':      cfg.get('track_threshold',   0.70),
        'interval':       cfg.get('track_interval',    1.0),
        'sound_enabled':  cfg.get('track_sound',       False),
        'sound_file':     cfg.get('track_sound_file',  None),
        'sound_duration': cfg.get('track_sound_dur',   5.0),
        'sound_volume':   cfg.get('track_sound_vol',   1.0),
    }

def set_tracking_prefs(prefs: dict) -> None:
    save_config({
        'track_threshold':  prefs.get('threshold',      0.70),
        'track_interval':   prefs.get('interval',       1.0),
        'track_sound':      prefs.get('sound_enabled',  False),
        'track_sound_file': prefs.get('sound_file',     None),
        'track_sound_dur':  prefs.get('sound_duration', 5.0),
        'track_sound_vol':  prefs.get('sound_volume',   1.0),
    })
