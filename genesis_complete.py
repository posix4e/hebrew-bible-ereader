#!/usr/bin/env python3
"""Generate just Genesis with all 50 chapters for testing"""

from kobo_fixed_toc import KoboOptimizedEPUB


class GenesisOnly(KoboOptimizedEPUB):
    def __init__(self):
        super().__init__()
        # Only Genesis
        self.torah_books = [
            ("Genesis", "בראשית", "Bereshit"),
        ]


if __name__ == "__main__":
    print("Generating complete Genesis (50 chapters)...")
    generator = GenesisOnly()
    generator.generate_kobo_epub("genesis_complete.epub")
