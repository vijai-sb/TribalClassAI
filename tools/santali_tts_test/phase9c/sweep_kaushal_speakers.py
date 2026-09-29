"""Phase 9C: sweep all 80 voices of kaushalkrishnax/santali-piper-vits at two sampling settings.

Usage:
  ..\\.venv\\Scripts\\python.exe sweep_kaushal_speakers.py <IndicConformer sat model.int8.onnx> <tokens.txt>

For each voice and setting, synthesizes each word N times and counts how often the independent
Santali ASR hears exactly the intended letters. Output is peak-normalized before ASR and saving
(the raw model output peaks around 0.06-0.09). Saves the best voice's clips for human listening.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import onnxruntime as ort
import sherpa_onnx
import soundfile as sf

HERE = Path(__file__).parent
MDIR = HERE / "kaushal"
sys.path.insert(0, str(MDIR))
from santhali_phonemizer import santhali_to_ipa  # noqa: E402

TESTS = [("book", "ᱯᱚᱛᱚᱵ"), ("one", "ᱢᱤᱫᱴᱟᱝ")]
SETTINGS = {"default (0.667, 1.0, 0.8)": (0.667, 1.0, 0.8), "calmer (0.333, 1.15, 0.333)": (0.333, 1.15, 0.333)}
N = 4


def ol_chiki(s):
    return re.sub(r"[^ᱚ-ᱽ]", "", unicodedata.normalize("NFC", s))


def main():
    cfg = json.loads((MDIR / "model" / "santali_piper_vits.onnx.json").read_text(encoding="utf-8"))
    sr, idm = cfg["audio"]["sample_rate"], cfg["phoneme_id_map"]
    sess = ort.InferenceSession(str(MDIR / "model" / "santali_piper_vits.onnx"), providers=["CPUExecutionProvider"])
    rec = sherpa_onnx.OfflineRecognizer.from_nemo_ctc(
        model=sys.argv[1], tokens=sys.argv[2], num_threads=4, sample_rate=16000, feature_dim=80,
        decoding_method="greedy_search")
    enc = {k: (t, idm["^"] + [x for ch in santhali_to_ipa(t) for x in idm[ch] + idm["_"]] + idm["$"]) for k, t in TESTS}

    def synth(ids, sid, scales):
        a = sess.run(None, {"input": np.array([ids], np.int64), "input_lengths": np.array([len(ids)], np.int64),
                            "scales": np.array(scales, np.float32), "sid": np.array([sid], np.int64)})[0].squeeze()
        return (a / (np.abs(a).max() + 1e-9) * 0.9).astype(np.float32)  # peak-normalize to -0.9 dBFS

    def heard(a):
        s = rec.create_stream()
        s.accept_waveform(sr, a)
        rec.decode_stream(s)
        return s.result.text.strip()

    out = HERE / "output_kaushal"
    out.mkdir(exist_ok=True)
    for label, scales in SETTINGS.items():
        per_voice = []
        totals = {k: 0 for k in enc}
        for sid in range(cfg["num_speakers"]):
            hits = {k: sum(ol_chiki(heard(synth(ids, sid, scales))) == ol_chiki(t) for _ in range(N))
                    for k, (t, ids) in enc.items()}
            for k in hits:
                totals[k] += hits[k]
            per_voice.append((hits["book"] + hits["one"], hits["book"], hits["one"], sid))
        per_voice.sort(reverse=True)
        n = cfg["num_speakers"] * N
        print(f"\n== {label}: exact matches over all 80 voices x {N}: "
              f"ᱯᱚᱛᱚᱵ {totals['book']}/{n} ({totals['book'] / n:.0%}), ᱢᱤᱫᱴᱟᱝ {totals['one']}/{n} ({totals['one'] / n:.0%})")
        print("   top voices (sid: book/one out of %d): " % N +
              ", ".join(f"{sid}: {b}/{o}" for _, b, o, sid in per_voice[:10]))
        print(f"   voices with 0/{2 * N}: {sum(1 for t, *_ in per_voice if t == 0)}")
        if label.startswith("calmer"):
            best = per_voice[0][3]
            for k, (t, ids) in enc.items():
                a = synth(ids, best, scales)
                p = out / f"santali_{k}_best_spk{best}_calmer.wav"
                sf.write(p, a, sr, subtype="PCM_16")
                print(f"   saved {p.name} ({len(a) / sr:.2f} s): ASR heard {heard(a) or '(nothing)'}")


if __name__ == "__main__":
    main()
