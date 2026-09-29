"""Make the prototype's pre-generated Santali clips louder and easier to hear on phone speakers.

Input: the original generated takes (*_nopad.wav / *_raw.wav). Output: processed/<name>.wav, padded
like pad_audio.py (300 ms lead, 200 ms tail). Timing, pitch and words are unchanged. Steps:
  1. 80 Hz high-pass (2nd-order Butterworth, run forward and backward: zero phase) - removes the DC
     offset and sub-80 Hz energy a phone speaker can't reproduce.
  2. Presence lift, +4 dB peak at 2.5 kHz (Q 0.9), zero phase. The TTS output has almost nothing above
     ~2 kHz; this only changes the tonal balance, it cannot restore missing high frequencies.
  3. Gain chosen so that speech RMS *after* limiting reaches TARGET_RMS_DBFS, with a smooth look-ahead
     peak limiter at CEILING_DBFS (gain curve = 20 ms running minimum, then 20 ms average, so it never
     overshoots; no hard clipping) doing at most MAX_LIMIT_DB of gain reduction.
  4. 5 ms fade in/out on the speech, then silence padding. 22,050 Hz mono 16-bit PCM WAV.

Usage (from this folder):  ..\\.venv\\Scripts\\python.exe process_audio.py
"""
import hashlib
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
OUT = HERE / "processed"
CLIPS = [("santali_book.wav", "santali_book_nopad.wav"), ("santali_one.wav", "santali_one_nopad.wav")]
LEAD_MS, TAIL_MS, FADE_MS = 300, 200, 5
TARGET_RMS_DBFS, CEILING_DBFS, MAX_LIMIT_DB = -13.0, -1.0, 6.0
GATE_DBFS = -40.0  # 20 ms frames above this count as speech for the RMS measurement


def read(path):
    with wave.open(str(path)) as w:
        assert (w.getnchannels(), w.getsampwidth()) == (1, 2), path
        return np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float64) / 32768, w.getframerate()


def biquad(x, b, a):
    b, a = np.asarray(b) / a[0], np.asarray(a) / a[0]
    y = np.zeros_like(x)
    x1 = x2 = y1 = y2 = 0.0
    for i, xi in enumerate(x):
        yi = b[0] * xi + b[1] * x1 + b[2] * x2 - a[1] * y1 - a[2] * y2
        x2, x1, y2, y1 = x1, xi, y1, yi
        y[i] = yi
    return y


def zero_phase(x, b, a, pad):
    # Reflect-pad so the filter settles before the signal, then run forward and backward.
    xp = np.concatenate([2 * x[0] - x[pad:0:-1], x, 2 * x[-1] - x[-2:-pad - 2:-1]])
    y = biquad(biquad(xp, b, a)[::-1], b, a)[::-1]
    return y[pad:pad + len(x)]


def highpass(fc, sr):  # RBJ cookbook, Butterworth Q
    w, q = 2 * np.pi * fc / sr, 1 / np.sqrt(2)
    al, c = np.sin(w) / (2 * q), np.cos(w)
    return [(1 + c) / 2, -(1 + c), (1 + c) / 2], [1 + al, -2 * c, 1 - al]


def peaking(fc, gain_db, q, sr):  # RBJ cookbook
    A, w = 10 ** (gain_db / 40), 2 * np.pi * fc / sr
    al, c = np.sin(w) / (2 * q), np.cos(w)
    return [1 + al * A, -2 * c, 1 - al * A], [1 + al / A, -2 * c, 1 - al / A]


def running(x, n, fn):
    xp = np.pad(x, (n // 2, n - 1 - n // 2), mode="edge")
    return fn(np.lib.stride_tricks.sliding_window_view(xp, n), axis=1)


def db(v):
    return 20 * np.log10(max(v, 1e-12))


def speech_rms(x, sr):
    f = int(sr * 0.02)
    fr = x[: len(x) // f * f].reshape(-1, f)
    keep = np.sqrt((fr ** 2).mean(1)) > 10 ** (GATE_DBFS / 20)
    return np.sqrt((fr[keep] ** 2).mean()), int(keep.sum() * 20)


def stats(x, sr):
    # Loudness is measured after the same 80 Hz high-pass for old and new files, so DC offset and
    # sub-80 Hz energy (inaudible on a phone speaker) don't count as loudness or as "speech".
    rms, ms = speech_rms(zero_phase(x, *highpass(80, sr), int(sr * 0.05)), sr)
    return {"dur_s": round(len(x) / sr, 3), "peak_dbfs": round(db(np.abs(x).max()), 2),
            "speech_rms_dbfs": round(db(rms), 2), "speech_ms": ms, "dc": round(float(x.mean()), 4),
            "clipped_samples": int((np.abs(x) >= 32767 / 32768).sum())}


def process(x, sr):
    pad = int(sr * 0.05)
    y = zero_phase(x, *highpass(80, sr), pad)
    y = zero_phase(y, *peaking(2500, 4.0 / 2, 0.9, sr), pad)  # half the gain per pass; two passes = +4 dB
    ceiling = 10 ** (CEILING_DBFS / 20)
    n = int(sr * 0.02)

    def limited(g):
        z = y * g
        need = np.minimum(1.0, ceiling / np.maximum(np.abs(z), 1e-12))
        gain = running(running(need, n, np.min), n, np.mean)
        return z * gain, -db(gain.min())

    # Bisect the make-up gain (dB) for the target post-limiter speech RMS, within the limiter budget.
    lo, hi = -20.0, 30.0
    for _ in range(40):
        mid = (lo + hi) / 2
        z, lim = limited(10 ** (mid / 20))
        if lim > MAX_LIMIT_DB or db(speech_rms(z, sr)[0]) > TARGET_RMS_DBFS:
            hi = mid
        else:
            lo = mid
    g_db = lo
    y, limit_db = limited(10 ** (g_db / 20))
    fade = int(sr * FADE_MS / 1000)
    ramp = np.linspace(0, 1, fade)
    y[:fade] *= ramp
    y[-fade:] *= ramp[::-1]
    return y, g_db, limit_db


def write(path, y, sr):
    pcm = np.round(np.clip(y, -1, 32767 / 32768) * 32768).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def main(clips=CLIPS):
    OUT.mkdir(exist_ok=True)
    for name, src in clips:
        x, sr = read(HERE / src)
        before = stats(np.concatenate([np.zeros(sr * LEAD_MS // 1000), x, np.zeros(sr * TAIL_MS // 1000)]), sr)
        y, gain_db, limit_db = process(x, sr)
        y = np.concatenate([np.zeros(sr * LEAD_MS // 1000), y, np.zeros(sr * TAIL_MS // 1000)])
        path = OUT / name
        write(path, y, sr)
        z, sr2 = read(path)  # verify what was actually written
        with wave.open(str(path)) as w:
            fmt = (w.getcomptype(), w.getnchannels(), w.getsampwidth() * 8, w.getframerate())
        after = stats(z, sr2)
        print(f"{name} (from {src}): gain {gain_db:+.1f} dB, limiter max {limit_db:.1f} dB | format {fmt} | "
              f"{path.stat().st_size} B | sha256 {hashlib.sha256(path.read_bytes()).hexdigest()[:16]}\n"
              f"  before (padded): {before}\n  after:           {after}")
        assert fmt == ("NONE", 1, 16, 22050) and after["clipped_samples"] == 0
        assert after["peak_dbfs"] <= CEILING_DBFS + 0.01 and abs(after["dur_s"] - before["dur_s"]) < 0.001


if __name__ == "__main__":
    main()
