"""Configuration for multiple translation EPUB"""

# Available English translations from Sefaria
TRANSLATIONS = {
    'default': {
        'name': 'Default Sefaria Translation',
        'param': None,  # Uses Sefaria's default
        'abbrev': 'SEF'
    },
    'jps_1917': {
        'name': 'The Holy Scriptures: A New Translation (JPS 1917)',
        'param': 'The Holy Scriptures: A New Translation (JPS 1917)',
        'abbrev': 'JPS1917'
    },
    'jps_1985': {
        'name': 'Tanakh: The Holy Scriptures, published by JPS',
        'param': 'Tanakh: The Holy Scriptures, published by JPS',
        'abbrev': 'JPS'
    },
    'contemporary': {
        'name': 'The Contemporary Torah, Jewish Publication Society, 2006',
        'param': 'The Contemporary Torah, Jewish Publication Society, 2006',
        'abbrev': 'CJPS'
    },
    'koren': {
        'name': 'The Koren Jerusalem Bible',
        'param': 'The Koren Jerusalem Bible',
        'abbrev': 'KJB'
    },
    'fox': {
        'name': 'The Five Books of Moses, by Everett Fox',
        'param': 'The Five Books of Moses, by Everett Fox. New York, Schocken Books, 1995',
        'abbrev': 'FOX'
    },
    'community': {
        'name': 'Sefaria Community Translation',
        'param': 'Sefaria Community Translation',
        'abbrev': 'SCT'
    },
    'metsudah': {
        'name': 'Metsudah Chumash',
        'param': 'Metsudah Chumash, Metsudah Publications, 2009',
        'abbrev': 'MET'
    }
}

# Combinations for the ultimate EPUB
TRANSLATION_COMBOS = [
    # Hebrew only
    ('hebrew_only', 'Hebrew Only', None),

    # Single English translations
    ('english_jps', 'English (JPS 1985)', 'jps_1985'),
    ('english_jps1917', 'English (JPS 1917)', 'jps_1917'),
    ('english_koren', 'English (Koren)', 'koren'),
    ('english_community', 'English (Community)', 'community'),

    # Hebrew with different English translations
    ('both_jps', 'Hebrew + JPS 1985', 'jps_1985'),
    ('both_jps1917', 'Hebrew + JPS 1917', 'jps_1917'),
    ('both_koren', 'Hebrew + Koren', 'koren'),

    # Multiple English translations side by side
    ('compare_jps', 'Compare: JPS 1917 vs 1985', ['jps_1917', 'jps_1985']),

    # With Rashi
    ('hebrew_rashi', 'Hebrew with Rashi', None),
    ('both_jps_rashi', 'Hebrew + JPS + Rashi', 'jps_1985')
]