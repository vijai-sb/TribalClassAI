"""Phase 9A: synthesize Ol Chiki text with sat_piper_model.onnx and measure it.

Usage:  .venv\\Scripts\\python.exe synthesize.py
Writes output/santali_book.wav and output/santali_one.wav and prints timings.

Uses plain onnxruntime with the standard Piper input encoding for a "text" voice:
[^] + for each character: [id, _] + [$], scales = [noise_scale, length_scale, noise_w].
"""
import json
import os
import time
import unicodedata
from pathlib import Path

import numpy as np
import onnxruntime as ort
import psutil
import soundfile as sf

HERE = Path(__file__).parent
MODEL = HERE / "model" / "sat_piper_model.onnx"
CONFIG = HERE / "model" / "sat_piper_model.onnx.json"
OUT = HERE / "output"

# The two existing phrase-pack translations; nothing else is synthesized.
TESTS = [("santali_book.wav", "ᱯᱚᱛᱚᱵ"), ("santali_one.wav", "ᱢᱤᱫᱴᱟᱝ")]
RUNS = 5  # timed repeats per phrase, after one warm-up


def encode(text, id_map):
    ids = list(id_map["^"])
    missing = []
    for ch in unicodedata.normalize("NFC", text):
        if ch not in id_map:
            missing.append(ch)
            continue
        ids += id_map[ch] + id_map["_"]
    return ids + id_map["$"], missing


def main():
    proc = psutil.Process(os.getpid())
    rss_before = proc.memory_info().rss
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    sr = cfg["audio"]["sample_rate"]
    inf = cfg["inference"]
    id_map = cfg["phoneme_id_map"]

    t = time.perf_counter()
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 4
    sess = ort.InferenceSession(str(MODEL), opts, providers=["CPUExecutionProvider"])
    load_ms = (time.perf_counter() - t) * 1000
    rss_loaded = proc.memory_info().rss
    print(f"inputs : {[(i.name, i.shape, i.type) for i in sess.get_inputs()]}")
    print(f"outputs: {[(o.name, o.shape) for o in sess.get_outputs()]}")
    print(f"model load: {load_ms:.0f} ms | RSS +{(rss_loaded - rss_before) / 2**20:.0f} MB")

    OUT.mkdir(exist_ok=True)
    scales = np.array([inf["noise_scale"], inf["length_scale"], inf["noise_w"]], dtype=np.float32)
    for name, text in TESTS:
        ids, missing = encode(text, id_map)
        if missing:
            raise SystemExit(f"{text!r}: characters not in model vocabulary: {missing}")
        feed = {
            "input": np.array([ids], dtype=np.int64),
            "input_lengths": np.array([len(ids)], dtype=np.int64),
            "scales": scales,
        }
        sess.run(None, feed)  # warm-up
        times = []
        for _ in range(RUNS):
            t = time.perf_counter()
            audio = sess.run(None, feed)[0].squeeze()
            times.append((time.perf_counter() - t) * 1000)
        # Piper output is float in [-1, 1]; write 16-bit PCM like the Piper CLI does.
        pcm = np.clip(audio, -1.0, 1.0)
        sf.write(OUT / name, pcm, sr, subtype="PCM_16")
        dur = len(pcm) / sr
        print(f"{name}: text={text} ids={ids} | {dur:.2f} s audio | synth median {np.median(times):.0f} ms "
              f"(min {min(times):.0f}, max {max(times):.0f}) | RTF {np.median(times) / 1000 / dur:.3f} "
              f"| peak {np.abs(pcm).max():.3f}")
    print(f"peak RSS after synthesis: {proc.memory_info().rss / 2**20:.0f} MB")


if __name__ == "__main__":
    main()
