"""Add short silence around the prototype clips so the start of the word is not lost while a
phone's audio output (speaker amplifier, Bluetooth link) wakes up. The speech itself is unchanged:
the original takes are kept as *_nopad.wav and the padded files replace santali_book/one.wav.

Usage (from this folder):  ..\\.venv\\Scripts\\python.exe pad_audio.py
"""
import hashlib
import shutil
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
LEAD_MS, TAIL_MS = 300, 200

for name in ("santali_book.wav", "santali_one.wav"):
    src = HERE / name
    orig = HERE / name.replace(".wav", "_nopad.wav")
    if not orig.exists():
        shutil.copy2(src, orig)  # keep the exact generated take
    with wave.open(str(orig)) as w:
        sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
        pcm = np.frombuffer(w.readframes(w.getnframes()), "<i2")
    out = np.concatenate([np.zeros(sr * LEAD_MS // 1000, "<i2"), pcm, np.zeros(sr * TAIL_MS // 1000, "<i2")])
    with wave.open(str(src), "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(sw)
        w.setframerate(sr)
        w.writeframes(out.tobytes())
    with wave.open(str(src)) as w:
        comp, nch, bits, rate, dur = w.getcomptype(), w.getnchannels(), w.getsampwidth() * 8, w.getframerate(), w.getnframes() / w.getframerate()
    print(f"{name}: speech {len(pcm) / sr:.3f} s + {LEAD_MS} ms lead + {TAIL_MS} ms tail = {dur:.3f} s | "
          f"PCM {comp} {nch} ch {bits}-bit {rate} Hz | {src.stat().st_size} B | "
          f"non-zero samples {int((out != 0).sum())} | peak {np.abs(out).max() / 32768:.2f} | "
          f"sha256 {hashlib.sha256(src.read_bytes()).hexdigest()}")
