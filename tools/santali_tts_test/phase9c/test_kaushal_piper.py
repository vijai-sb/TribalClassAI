"""Phase 9C: test kaushalkrishnax/santali-piper-vits (commit ba883eed) on the two phrase-pack words.

Usage:
  ..\\.venv\\Scripts\\python.exe test_kaushal_piper.py <IndicConformer sat model.int8.onnx> <tokens.txt>

Pipeline (as documented by the model card): Ol Chiki -> santhali_to_ipa() -> phoneme_id_map
-> Piper ids [^] + (id, _)* + [$] -> ONNX (input, input_lengths, scales, sid) -> 22.05 kHz audio.

Intelligibility is checked with AI4Bharat IndicConformer Santali (independent ASR). A match means an
independent recogniser heard the intended letters; it is not a native-speaker judgement.
"""
import json
import os
import re
import sys
import time
import unicodedata
import wave
from pathlib import Path

import numpy as np
import onnxruntime as ort
import psutil
import sherpa_onnx
import soundfile as sf

HERE = Path(__file__).parent
MDIR = HERE / "kaushal"
sys.path.insert(0, str(MDIR))
from santhali_phonemizer import santhali_to_ipa  # noqa: E402  (reviewed: pure string processing)

OUT = HERE / "output_kaushal"
TESTS = [("book", "ᱯᱚᱛᱚᱵ"), ("one", "ᱢᱤᱫᱴᱟᱝ")]
SPEAKERS_TO_SAVE = [0]            # default speaker: saved as the primary sample
SPEAKER_SWEEP = list(range(0, 80, 8))  # 10 of the 80 voices for the ASR check
VARIANTS = 3                     # random-sampling repeats per voice


def ol_chiki(s):
    return re.sub(r"[^ᱚ-ᱽ]", "", unicodedata.normalize("NFC", s))


def cer(ref, hyp):
    r, h = ol_chiki(ref), ol_chiki(hyp)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1]))
    return d[len(h)] / max(1, len(r))


def main():
    asr_model, tokens = sys.argv[1], sys.argv[2]
    proc = psutil.Process(os.getpid())
    cfg = json.loads((MDIR / "model" / "santali_piper_vits.onnx.json").read_text(encoding="utf-8"))
    sr, idm, inf = cfg["audio"]["sample_rate"], cfg["phoneme_id_map"], cfg["inference"]
    scales = np.array([inf["noise_scale"], inf["length_scale"], inf["noise_w"]], np.float32)

    rss0 = proc.memory_info().rss
    t = time.perf_counter()
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 4
    sess = ort.InferenceSession(str(MDIR / "model" / "santali_piper_vits.onnx"), opts,
                                providers=["CPUExecutionProvider"])
    load_ms = (time.perf_counter() - t) * 1000
    print(f"inputs: {[(i.name, i.shape) for i in sess.get_inputs()]}")
    print(f"model load {load_ms:.0f} ms | RSS +{(proc.memory_info().rss - rss0) / 2**20:.0f} MB")

    def synth(ids, sid):
        feed = {"input": np.array([ids], np.int64), "input_lengths": np.array([len(ids)], np.int64),
                "scales": scales, "sid": np.array([sid], np.int64)}
        return np.clip(sess.run(None, feed)[0].squeeze(), -1, 1)

    rec = sherpa_onnx.OfflineRecognizer.from_nemo_ctc(
        model=asr_model, tokens=tokens, num_threads=4, sample_rate=16000, feature_dim=80,
        decoding_method="greedy_search")

    def asr(audio):
        s = rec.create_stream()
        s.accept_waveform(sr, audio.astype(np.float32))  # sherpa-onnx resamples 22.05 kHz -> 16 kHz
        rec.decode_stream(s)
        return s.result.text.strip()

    OUT.mkdir(exist_ok=True)
    encoded = {}
    print("\n== synthesis timing and saved samples (speaker 0)")
    for key, text in TESTS:
        ipa = santhali_to_ipa(text)
        ids = idm["^"] + [x for ch in ipa for x in idm[ch] + idm["_"]] + idm["$"]
        encoded[key] = (text, ids)
        synth(ids, 0)  # warm-up
        times = []
        for _ in range(5):
            t = time.perf_counter()
            audio = synth(ids, 0)
            times.append((time.perf_counter() - t) * 1000)
        path = OUT / f"santali_{key}_spk0.wav"
        sf.write(path, audio, sr, subtype="PCM_16")
        with wave.open(str(path)) as w:
            fmt = f"{w.getframerate()} Hz, {w.getnchannels()} ch, {w.getsampwidth() * 8}-bit"
        dur = len(audio) / sr
        print(f"{path.name}: {text} -> IPA '{ipa}' | {path.stat().st_size} B | {fmt} | {dur:.2f} s | "
              f"synth median {np.median(times):.0f} ms (min {min(times):.0f}, max {max(times):.0f}) | "
              f"RTF {np.median(times) / 1000 / dur:.3f} | peak {np.abs(audio).max():.2f} | "
              f"ASR heard: {asr(audio) or '(nothing)'}")
    print(f"process RSS after synthesis: {proc.memory_info().rss / 2**20:.0f} MB")

    print(f"\n== ASR check: {len(SPEAKER_SWEEP)} voices x {VARIANTS} samples per word")
    for key, (text, ids) in encoded.items():
        heard, cers = [], []
        for sid in SPEAKER_SWEEP:
            for v in range(VARIANTS):
                audio = synth(ids, sid)
                h = asr(audio)
                heard.append(f"s{sid}:{h or '∅'}")
                cers.append(cer(text, h))
                if v == 0 and sid in (8, 40):  # keep two extra voices for human listening
                    sf.write(OUT / f"santali_{key}_spk{sid}.wav", audio, sr, subtype="PCM_16")
        exact = sum(c == 0 for c in cers)
        near = sum(c <= 0.34 for c in cers)
        print(f"{text}: exact {exact}/{len(cers)} | CER<=0.34 {near}/{len(cers)} | median CER {np.median(cers):.2f}")
        print("   heard: " + ", ".join(heard))


if __name__ == "__main__":
    main()
