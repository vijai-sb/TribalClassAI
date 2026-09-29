"""Phase 9A: validate the generated WAVs and run an ASR intelligibility proxy.

Usage:  .venv\\Scripts\\python.exe evaluate.py <santali_asr_model.int8.onnx> <tokens.txt>

The ASR model is AI4Bharat IndicConformer Santali (CTC, int8, sherpa-onnx), the same family
already used for Hindi in the app. A matching transcript means an independent Santali
recogniser heard the intended letters. It is NOT a native-speaker judgement of pronunciation
or naturalness, and a mismatch does not prove the audio is wrong.
"""
import json
import re
import sys
import unicodedata
import wave
from pathlib import Path

import numpy as np
import onnxruntime as ort
import sherpa_onnx
import soundfile as sf

HERE = Path(__file__).parent
OUT = HERE / "output"
TARGETS = {"santali_book.wav": "ᱯᱚᱛᱚᱵ", "santali_one.wav": "ᱢᱤᱫᱴᱟᱝ"}
VARIANTS = 10  # extra syntheses per phrase: Piper sampling is random (noise_scale, noise_w)


def ol_chiki(s):
    return re.sub(r"[^ᱚ-ᱽ]", "", unicodedata.normalize("NFC", s))  # letters only


def cer(ref, hyp):
    r, h = ol_chiki(ref), ol_chiki(hyp)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1]))
    return d[len(h)] / max(1, len(r))


def speech_span(a, sr, db=-40):
    """Seconds between first and last 20 ms frame within `db` of the peak."""
    f = int(sr * 0.02)
    frames = a[: len(a) // f * f].reshape(-1, f)
    rms = np.sqrt((frames ** 2).mean(1)) + 1e-9
    on = np.where(20 * np.log10(rms / rms.max()) > db)[0]
    return (on[-1] - on[0] + 1) * f / sr if len(on) else 0.0


def main():
    asr_model, tokens = sys.argv[1], sys.argv[2]
    rec = sherpa_onnx.OfflineRecognizer.from_nemo_ctc(
        model=asr_model, tokens=tokens, num_threads=4, sample_rate=16000,
        feature_dim=80, decoding_method="greedy_search")

    def transcribe(audio, sr):
        s = rec.create_stream()
        s.accept_waveform(sr, audio.astype(np.float32))
        rec.decode_stream(s)
        return s.result.text.strip()

    print("== WAV validation (generated files)")
    for name in TARGETS:
        p = OUT / name
        with wave.open(str(p)) as w:  # stdlib parser: proves a well-formed RIFF/WAVE file
            ch, width, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        a, _ = sf.read(p, dtype="float32")
        print(f"{name}: {p.stat().st_size} bytes | {sr} Hz | {ch} ch | {width * 8}-bit PCM | "
              f"{n / sr:.2f} s | speech span {speech_span(a, sr):.2f} s | "
              f"RMS {np.sqrt((a ** 2).mean()):.3f} | clipped samples {(np.abs(a) >= 0.999).sum()}")

    print("\n== ASR proxy on the saved outputs")
    for name, ref in TARGETS.items():
        a, sr = sf.read(OUT / name, dtype="float32")
        hyp = transcribe(a, sr)
        print(f"{name}: intended {ref} | ASR heard {hyp or '(nothing)'} | CER {cer(ref, hyp):.2f}")

    print(f"\n== ASR proxy on {VARIANTS} fresh syntheses per phrase (sampling varies run to run)")
    cfg = json.loads((HERE / "model" / "sat_piper_model.onnx.json").read_text(encoding="utf-8"))
    idm, inf = cfg["phoneme_id_map"], cfg["inference"]
    sess = ort.InferenceSession(str(HERE / "model" / "sat_piper_model.onnx"), providers=["CPUExecutionProvider"])
    scales = np.array([inf["noise_scale"], inf["length_scale"], inf["noise_w"]], dtype=np.float32)
    for name, ref in TARGETS.items():
        ids = idm["^"] + [x for ch in ref for x in idm[ch] + idm["_"]] + idm["$"]
        feed = {"input": np.array([ids], np.int64), "input_lengths": np.array([len(ids)], np.int64), "scales": scales}
        hyps = [transcribe(np.clip(sess.run(None, feed)[0].squeeze(), -1, 1), cfg["audio"]["sample_rate"])
                for _ in range(VARIANTS)]
        cers = [cer(ref, h) for h in hyps]
        exact = sum(c == 0 for c in cers)
        print(f"{ref}: exact {exact}/{VARIANTS} | median CER {np.median(cers):.2f} | heard: {', '.join(h or '∅' for h in hyps)}")

    print("\n== Reference: the repository's own sample clips (intended text not published)")
    for p in sorted((HERE / "repo_samples").glob("*.wav")):
        a, sr = sf.read(p, dtype="float32", always_2d=True)
        a = a.mean(1)
        print(f"{p.name}: {sr} Hz | {len(a) / sr:.2f} s | ASR heard {transcribe(a, sr) or '(nothing)'}")


if __name__ == "__main__":
    main()
