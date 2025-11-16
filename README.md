# Hebrew Bible EPUB Generator for Kobo Color

Generate beautiful, readable Hebrew Bible EPUBs optimized for Kobo Color e-readers with parallel Hebrew/English text, commentary, and responsive layouts.

## Features

- **Parallel Text Display**: Side-by-side Hebrew and English in landscape mode, stacked in portrait
- **Multiple Translation Options**: Default Sefaria, JPS (1985), Koren Jerusalem Bible, and more
- **Commentary Support**: Rashi commentary included as footnotes (optional)
- **Torah Portions (Parshiyot)**: Weekly Torah reading markers
- **Responsive Design**: Optimized specifically for Kobo Color's 7" screen
- **Language Options**: Generate Hebrew-only, English-only, or both
- **Book Selection**: Choose Torah, Prophets, or both

## Installation

1. Install Python 3.8 or higher
2. Clone this repository
3. Install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Quick Start

### Interactive Mode (Recommended)

```bash
python generate.py
```

This will guide you through all configuration options.

### Command Line Options

```bash
# Hebrew text only
python generate.py --hebrew-only -o torah_hebrew.epub

# English text only
python generate.py --english-only -o torah_english.epub

# Torah only with Rashi
python generate.py --torah --rashi -o torah_rashi.epub

# Prophets only
python generate.py --prophets -o prophets.epub
```

### Generate Sample

To quickly test with just a few chapters:

```bash
python generate_sample.py
```

### Generate Full Books

For complete Torah and Prophets:

```bash
# All books
python generate_full.py

# Torah only
python generate_full.py torah

# Prophets only
python generate_full.py prophets
```

## Configuration Options

Edit `config.py` to customize:

- **Display Mode**: `'hebrew'`, `'english'`, or `'both'`
- **Translation Version**: Various English translations available
- **Layout**: Side-by-side vs stacked in landscape mode
- **Commentary**: Include/exclude Rashi commentary
- **Formatting**: Verse numbers, parsha markers, font sizes

## Transferring to Kobo

1. Connect your Kobo Color via USB
2. Copy the `.epub` file to the Kobo's root directory
3. Safely eject and the book will appear in your library

## Layout on Kobo Color

The EPUB is optimized for Kobo Color's screen:
- **Portrait Mode**: Hebrew text above, English below each verse
- **Landscape Mode**: Hebrew and English side-by-side
- **Font Adjustment**: Use Kobo's built-in controls to adjust size

## API Usage

This tool uses the free Sefaria API for biblical texts. Please be respectful of their servers - the generator includes delays between requests.

## Books Included

### Torah (Five Books of Moses)
- Genesis (Bereshit)
- Exodus (Shemot)
- Leviticus (Vayikra)
- Numbers (Bamidbar)
- Deuteronomy (Devarim)

### Prophets (Nevi'im)
- Joshua through Malachi (21 books)

## Known Limitations

- Kobo's EPUB renderer may not perfectly display all Hebrew fonts
- Complex commentary layouts work best in portrait mode
- Large files (full Tanakh) may load slowly on e-ink devices

## Troubleshooting

- **Hebrew text not displaying**: Ensure your Kobo has Hebrew font support
- **Slow page turns**: Try generating smaller files (Torah or Prophets only)
- **Layout issues**: Adjust Kobo's margin and line spacing settings

## Future Enhancements

- [ ] Ketuvim (Writings) support
- [ ] More commentary options (Ibn Ezra, Ramban, etc.)
- [ ] Cross-references between verses
- [ ] Search functionality
- [ ] Custom font embedding

## License

This tool is provided as-is for personal use. Biblical texts are from Sefaria's open-source library.