"""Configuration for Hebrew Bible EPUB generation"""

class BibleConfig:
    """Configuration settings for EPUB generation"""

    # Language display options
    DISPLAY_MODE = 'both'  # Options: 'hebrew', 'english', 'both'

    # Translation versions available from Sefaria
    ENGLISH_VERSION = 'default'  # Options: 'default', 'JPS', 'Koren', 'Sefaria Community'

    # Layout preferences
    SIDE_BY_SIDE_IN_LANDSCAPE = True  # Use side-by-side in landscape mode
    VERSE_NUMBERS = True  # Show verse numbers

    # Commentary and notes
    INCLUDE_RASHI = False  # Include Rashi commentary as footnotes
    INCLUDE_CROSS_REFERENCES = False  # Include cross-references

    # Books to include
    INCLUDE_TORAH = True
    INCLUDE_PROPHETS = True
    INCLUDE_WRITINGS = False  # Ketuvim (not implemented yet)

    # Formatting
    PARSHA_MARKERS = True  # Show weekly Torah portion markers
    CHAPTER_HEBREW_NAMES = True  # Use Hebrew chapter names

    # Font settings
    HEBREW_FONT_SIZE = '1.2em'
    ENGLISH_FONT_SIZE = '1.0em'

    # API settings
    API_DELAY = 0.1  # Delay between API calls in seconds

    @classmethod
    def from_dict(cls, config_dict):
        """Create config from dictionary"""
        config = cls()
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config