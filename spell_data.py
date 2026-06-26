"""
spell_data.py — Sorts Dofus Rétro par classe.
Images : spells/<classe>/9-1.png à 9-22.png (sorts classe)
         spells/<classe>/99-23.png à 99-30.png (sorts communs)
"""

_COMMUNS = [
    {'nom': 'Cawotte',                'img': '99-23'},
    {'nom': 'Flamiche',               'img': '99-24'},
    {'nom': 'Marteau de Moon',        'img': '99-25'},
    {'nom': 'Boomerang Perfide',      'img': '99-26'},
    {'nom': 'Foudroiement',           'img': '99-27'},
    {'nom': 'Libération',             'img': '99-28'},
    {'nom': 'Invocation de Chaferfu', 'img': '99-29'},
    {"nom": "Invocation d'Arakne",    'img': '99-30'},
]

SPELLS = {
    'cra': [
        {'nom': 'Flèche Empoisonnée',     'img': '9-1'},
        {'nom': 'Flèche de Recul',         'img': '9-2'},
        {'nom': 'Flèche Magique',          'img': '9-3'},
        {'nom': 'Flèche Glacée',           'img': '9-4'},
        {'nom': 'Flèche Enflammée',        'img': '9-5'},
        {'nom': 'Tir Éloigné',             'img': '9-6'},
        {"nom": "Flèche d'Expiation",      'img': '9-7'},
        {'nom': 'Oeil de Taupe',           'img': '9-8'},
        {'nom': 'Tir Critique',            'img': '9-9'},
        {"nom": "Flèche d'Immobilisation", 'img': '9-10'},
        {'nom': 'Flèche Punitive',         'img': '9-11'},
        {'nom': 'Tir Puissant',            'img': '9-12'},
        {'nom': 'Flèche Harcelante',       'img': '9-13'},
        {'nom': 'Flèche Cinglante',        'img': '9-14'},
        {'nom': 'Flèche Persécutrice',     'img': '9-15'},
        {'nom': 'Flèche Destructrice',     'img': '9-16'},
        {'nom': 'Flèche Absorbante',       'img': '9-17'},
        {'nom': 'Flèche Ralentissante',    'img': '9-18'},
        {'nom': 'Flèche Explosive',        'img': '9-19'},
        {"nom": "Maîtrise de l'Arc",       'img': '9-20'},
        {'nom': 'Invocation du Dopeul',    'img': '9-21'},
        {'nom': 'Flèche de Dispersion',    'img': '9-22'},
    ] + _COMMUNS,

    'enu': [
        {'nom': 'Sac Animé',               'img': '3-1'},
        {'nom': 'Lancer de Pièces',        'img': '3-2'},
        {'nom': 'Lancer de Pelle',         'img': '3-3'},
        {'nom': 'Pelle Fantomatique',      'img': '3-4'},
        {'nom': 'Chance',                  'img': '3-5'},
        {'nom': 'Boîte de Pandore',        'img': '3-6'},
        {'nom': 'Remblai',                 'img': '3-7'},
        {'nom': 'Clé Réductrice',          'img': '3-8'},
        {"nom": "Force de l'Age",          'img': '3-9'},
        {'nom': 'Désinvocation',           'img': '3-10'},
        {'nom': 'Cupidité',                'img': '3-11'},
        {'nom': 'Roulage de Pelle',        'img': '3-12'},
        {'nom': 'Maladresse',              'img': '3-13'},
        {'nom': 'Maladresse de Masse',     'img': '3-14'},
        {'nom': 'Accélération',            'img': '3-15'},
        {'nom': 'Pelle du Jugement',       'img': '3-16'},
        {'nom': 'Pelle Massacrante',       'img': '3-17'},
        {'nom': 'Corruption',              'img': '3-18'},
        {'nom': 'Pelle Animée',            'img': '3-19'},
        {'nom': 'Coffre Animé',            'img': '3-20'},
        {'nom': 'Invocation du Dopeul',    'img': '3-21'},
        {'nom': 'Retraite Anticipée',      'img': '3-22'},
    ] + _COMMUNS,

    'pan': [
        {'nom': 'Picole',                          'img': '12-1'},
        {'nom': 'Poing Enflammé',                  'img': '12-2'},
        {'nom': 'Gueule de Bois',                  'img': '12-3'},
        {'nom': 'Epouvante',                       'img': '12-4'},
        {'nom': 'Souffle Alcoolisé',               'img': '12-5'},
        {'nom': 'Vulnérabilité Aqueuse',           'img': '12-6'},
        {'nom': 'Vulnérabilité Incandescente',     'img': '12-7'},
        {'nom': 'Karcham',                         'img': '12-8'},
        {'nom': 'Vulnérabilité Venteuse',          'img': '12-9'},
        {'nom': 'Stabilisation',                   'img': '12-10'},
        {'nom': 'Chamrak',                         'img': '12-11'},
        {'nom': 'Vulnérabilité Terrestre',         'img': '12-12'},
        {'nom': 'Souillure',                       'img': '12-13'},
        {'nom': 'Lait de Bambou',                  'img': '12-14'},
        {'nom': 'Vague à Lame',                    'img': '12-15'},
        {'nom': 'Colère de Zatoïshwan',            'img': '12-16'},
        {'nom': 'Flasque Explosive',               'img': '12-17'},
        {'nom': 'Pandatak',                        'img': '12-18'},
        {'nom': 'Pandanlku',                       'img': '12-19'},
        {'nom': 'Lien Spirituel',                  'img': '12-20'},
        {'nom': 'Invocation du Dopeul',            'img': '12-21'},
        {'nom': 'Ivresse',                         'img': '12-22'},
    ] + _COMMUNS,
}

CLASS_FOLDER = {
    'cra': 'spells/cra',
    'enu': 'spells/enu',
    'pan': 'spells/pan',
}

CLASS_COLORS = {
    'cra': {'primary': '#6a9e3f', 'light': '#8abf55', 'name': 'Cra'},
    'enu': {'primary': '#c09020', 'light': '#d4aa44', 'name': 'Enutrof'},
    'pan': {'primary': '#7844aa', 'light': '#9966cc', 'name': 'Pandawa'},
}
