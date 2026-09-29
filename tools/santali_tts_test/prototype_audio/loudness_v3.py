"""Louder versions of the shipped Santali clips for a live demo (v3), rendered at several loudness targets.

Starts again from the original TTS takes (not from the already-processed files), applies the same
80 Hz high-pass and +4 dB presence lift as process_audio.py, then:
  - a speech compressor (RMS detector 5 ms, threshold 10 dB below the speech RMS, ratio RATIO,
    attack 2 ms / release 60 ms on the gain in dB) to reduce the level gap between loud and soft syllables,
  - make-up gain found by bisection so the padded file reaches the target integrated loudness,
    but never more than the limiter budget allows (MAX_LIMIT_DB / MAX_COMP_DB): if the target
    can't be reached within it, the file stays at the loudest level that stays within it,
  - a true-peak limiter: required gain computed on the 4x-oversampled signal, 10 ms look-ahead
    (running minimum, then running mean, so it never overshoots), ceiling CEILING_DBTP,
  - 5 ms edge fades and the same 300/200 ms silence padding.
Writes loud_candidates/<name>_<target>.wav and loud_candidates/summary.json. Nothing in res/raw is touched.
The Santali ASR check (asr_check.py) and the choice of target happen afterwards.

Usage (from this folder):  ..\\..\\indictrans2_test\\.venv\\Scripts\\python.exe loudness_v3.py
"""
import json
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
from scipy.signal import resample_poly

import process_audio as P

HERE = Path(__file__).parent
OUT = HERE / "loud_candidates"
SOURCES = {  # shipped file -> original generated take
    "santali_book": "santali_book_nopad.wav",
    "santali_one": "santali_one_nopad.wav",
    "santali_very_good": "santali_very_good_raw.wav",
    "santali_what_is_your_name": "santali_your_name_raw.wav",
}
TARGETS_LUFS = [-10.0, -11.0, -12.0, -13.0, -14.0]
RATIO, ATTACK_MS, RELEASE_MS = 4.0, 2.0, 60.0
MAX_LIMIT_DB, MAX_COMP_DB = 6.0, 12.0
CEILING_DBTP = -1.0
LEAD_MS, TAIL_MS, FADE_MS = 300, 200, 5


def db(v):
    return 20 * np.log10(np.maximum(v, 1e-12))


def true_peak(x):
    return np.abs(resample_poly(x, 4, 1)).max()


def compress(x, sr):
    n = int(sr * 0.005)
    level = db(np.sqrt(P.running(x ** 2, n, np.mean)))
    rms, _ = P.speech_rms(x, sr)
    thr = db(rms) - 10.0
    target_gr = np.minimum(np.where(level > thr, (level - thr) * (1 - 1 / RATIO), 0.0), MAX_COMP_DB)
    a = np.exp(-1 / (sr * ATTACK_MS / 1000))
    r = np.exp(-1 / (sr * RELEASE_MS / 1000))
    gr = np.zeros_like(x)
    g = 0.0
    for i, t in enumerate(target_gr):
        c = a if t > g else r  # more reduction: attack; less: release
        g = c * g + (1 - c) * t
        gr[i] = g
    return x * 10 ** (-gr / 20), float(gr.max())


def tp_limit(x, ceiling):
    up = np.abs(resample_poly(x, 4, 1))[: len(x) * 4].reshape(len(x), 4).max(1)
    need = np.minimum(1.0, ceiling / np.maximum(up, 1e-12))
    n = int(22050 * 0.01)
    gain = P.running(P.running(need, n, np.min), n, np.mean)
    return x * gain, float(-db(gain.min()))


def pad(x, sr):
    return np.concatenate([np.zeros(sr * LEAD_MS // 1000), x, np.zeros(sr * TAIL_MS // 1000)])


def render(x, sr, target, meter):
    pre = P.zero_phase(x, *P.highpass(80, sr), int(sr * 0.05))
    pre = P.zero_phase(pre, *P.peaking(2500, 4.0 / 2, 0.9, sr), int(sr * 0.05))
    comp, comp_gr = compress(pre, sr)
    ceiling = 10 ** (CEILING_DBTP / 20)

    def build(gain_db, ceil):
        y, lim = tp_limit(comp * 10 ** (gain_db / 20), ceil)
        f = int(sr * FADE_MS / 1000)
        ramp = np.linspace(0, 1, f)
        y[:f] *= ramp
        y[-f:] *= ramp[::-1]
        return pad(y, sr), lim

    lo, hi = -20.0, 40.0
    for _ in range(40):
        mid = (lo + hi) / 2
        y, lim = build(mid, ceiling)
        if lim > MAX_LIMIT_DB or meter.integrated_loudness(y) > target:
            hi = mid
        else:
            lo = mid
    y, lim = build(lo, ceiling)
    # 16-bit rounding can nudge the true peak; tighten the ceiling until the written signal is under it.
    for _ in range(5):
        q = np.round(np.clip(y, -1, 32767 / 32768) * 32768) / 32768
        if true_peak(q) <= ceiling:
            break
        ceiling *= 10 ** (-0.05 / 20)
        y, lim = build(lo, ceiling)
    return y, lo, comp_gr, lim


def main():
    OUT.mkdir(exist_ok=True)
    summary = {}
    for name, src in SOURCES.items():
        x, sr = P.read(HERE / src)
        meter = pyln.Meter(sr, block_size=0.2)
        for target in TARGETS_LUFS:
            y, gain_db, comp_gr, lim = render(x, sr, target, meter)
            path = OUT / f"{name}_{int(-target)}.wav"
            P.write(path, y, sr)
            z, _ = P.read(path)
            s = {"target_lufs": target, "lufs": round(meter.integrated_loudness(z), 2),
                 "sample_peak_dbfs": round(float(db(np.abs(z).max())), 2), "true_peak_dbtp": round(float(db(true_peak(z))), 2),
                 "clipped_samples": int((np.abs(z) >= 32767 / 32768).sum()), "makeup_db": round(gain_db, 1),
                 "compressor_max_gr_db": round(comp_gr, 1), "limiter_max_gr_db": round(lim, 1),
                 "dur_s": round(len(z) / sr, 3), "bytes": path.stat().st_size}
            summary[path.name] = s
            print(path.name, s)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
