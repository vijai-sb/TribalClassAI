"""Stage 1 standalone test: run Whisper STT on a local audio file.

Usage:
    python scripts/test_stt.py path\\to\\audio.wav

Any format ffmpeg/PyAV can decode works (wav, mp3, m4a, webm...).
Record a short Hindi or English sentence with Windows Voice Recorder (or your
phone) and point this script at the file to sanity-check this stage alone.
"""

import sys
from pathlib import Path

# Windows terminals default to a legacy codepage (e.g. cp1252) that can't
# print Devanagari text; force UTF-8 so Hindi transcripts don't crash print().
sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stt import transcribe  # noqa: E402


def main():
    if len(sys.argv) != 2:
        print("Usage: python test_stt.py <path-to-audio-file>")
        sys.exit(1)
    audio_path = sys.argv[1]
    print(f"Loading Whisper and transcribing {audio_path} ...")
    result = transcribe(audio_path)
    print(f"Detected language: {result['language']}")
    print(f"Transcribed text : {result['text']}")


if __name__ == "__main__":
    main()
