"""Stage 3 standalone test: synthesize Santali speech with Indic Parler-TTS.

Usage:
    python scripts/test_tts.py "some santali text" output.wav
"""

import sys
from pathlib import Path

import soundfile as sf

# Windows terminals default to a legacy codepage (e.g. cp1252) that can't
# print Ol Chiki text.
sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tts import synthesize  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print('Usage: python test_tts.py "santali text" [output.wav]')
        sys.exit(1)
    text = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "tts_output.wav"
    print("Loading Indic Parler-TTS and generating audio (can take a while on CPU) ...")
    audio, sample_rate = synthesize(text)
    sf.write(out_path, audio, sample_rate)
    print(f"Wrote {out_path} ({len(audio) / sample_rate:.2f}s @ {sample_rate}Hz)")


if __name__ == "__main__":
    main()
