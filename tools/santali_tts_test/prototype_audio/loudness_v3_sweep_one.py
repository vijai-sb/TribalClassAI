"""santali_one got worse on the Santali ASR check with loudness_v3's default compressor, so render it with
progressively gentler settings to find the loudest one that is no worse than the shipped file.

Each setting: (compressor ratio, threshold in dB below the speech RMS, max compressor GR, max limiter GR).
Output: loud_candidates/one_sweep/*.wav; check them with asr_check.py.

Usage (from this folder):  ..\\..\\indictrans2_test\\.venv\\Scripts\\python.exe loudness_v3_sweep_one.py
"""
import numpy as np
import pyloudnorm as pyln

import loudness_v3 as L
import process_audio as P

SETTINGS = [(1.0, 0, 0, 6), (2.0, 6, 6, 6), (2.0, 10, 8, 6), (3.0, 6, 8, 6), (3.0, 10, 10, 6), (4.0, 10, 12, 4)]


def make_compress(thr_below):
    def compress(v, sr):
        n = int(sr * 0.005)
        level = L.db(np.sqrt(P.running(v ** 2, n, np.mean)))
        rms, _ = P.speech_rms(v, sr)
        t = L.db(rms) - thr_below
        tgr = np.minimum(np.where(level > t, (level - t) * (1 - 1 / L.RATIO), 0.0), L.MAX_COMP_DB)
        a = np.exp(-1 / (sr * L.ATTACK_MS / 1000))
        r = np.exp(-1 / (sr * L.RELEASE_MS / 1000))
        gr = np.zeros_like(v)
        g = 0.0
        for i, tt in enumerate(tgr):
            c = a if tt > g else r
            g = c * g + (1 - c) * tt
            gr[i] = g
        return v * 10 ** (-gr / 20), float(gr.max())
    return compress


def main():
    out = L.HERE / "loud_candidates" / "one_sweep"
    out.mkdir(parents=True, exist_ok=True)
    x, sr = P.read(L.HERE / "santali_one_nopad.wav")
    meter = pyln.Meter(sr, block_size=0.2)
    for ratio, thr, comp_cap, lim_cap in SETTINGS:
        L.RATIO, L.MAX_COMP_DB, L.MAX_LIMIT_DB = ratio, comp_cap, lim_cap
        L.compress = make_compress(thr)
        y, _, cg, lg = L.render(x, sr, -10.0, meter)
        path = out / f"one_r{ratio}_t{thr}_c{comp_cap}_l{lim_cap}.wav"
        P.write(path, y, sr)
        z, _ = P.read(path)
        print(f"{path.name} | LUFS {meter.integrated_loudness(z):.2f} | TP {float(L.db(L.true_peak(z))):.2f} dBTP | "
              f"compressor {cg:.1f} dB | limiter {lg:.1f} dB | clipped {int((np.abs(z) >= 32767 / 32768).sum())}")


if __name__ == "__main__":
    main()
