"""Stage 2 standalone test: translate Hindi/English text to Santali (Ol Chiki).

Usage:
    python scripts/test_translate.py en "Good morning children, open your books."
    python scripts/test_translate.py hi "बच्चों सुप्रभात, अपनी किताबें खोलो।"
"""

import sys
from pathlib import Path

# Windows terminals default to a legacy codepage (e.g. cp1252) that can't
# print Devanagari/Ol Chiki text; force UTF-8 so this script doesn't crash
# on print() even though the translation itself succeeded.
sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from translate import translate_to_santali  # noqa: E402


def main():
    if len(sys.argv) != 3:
        print('Usage: python test_translate.py <en|hi> "text to translate"')
        sys.exit(1)
    lang, text = sys.argv[1], sys.argv[2]
    print("Loading translation model and translating ...")
    santali = translate_to_santali(text, lang)
    print(f"Source ({lang}): {text}")
    print(f"Santali (sat_Olck): {santali}")


if __name__ == "__main__":
    main()
