"""Generate the prototype's pre-generated Santali speech clips.

Usage (from this folder):
  ..\\.venv\\Scripts\\python.exe generate_prototype_audio.py <IndicConformer sat model.int8.onnx> <tokens.txt>

Model: kaushalkrishnax/santali-piper-vits (commit ba883eed), speaker 7, settings (0.333, 1.15, 0.333) —
the voice and settings chosen in Phase 9C. For each phrase-pack word it synthesizes up to MAX_TAKES takes
and keeps the first one the independent Santali ASR transcribes exactly (a quality filter, not proof of
correctness). Output: peak-normalised 16-bit mono PCM WAV at the model's 22,050 Hz.
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
MDIR = HERE.parent / "phase9c" / "kaushal"
sys.path.insert(0, str(MDIR))
from santhali_phonemizer import santhali_to_ipa  # noqa: E402  (reviewed in Phase 9C: string rules only)

# Exactly the Santali entries in app/.../data/OfflinePhrasePack.kt; nothing else.
PHRASES = [("santali_book.wav", "किताब", "ᱯᱚᱛᱚᱵ"), ("santali_one.wav", "एक", "ᱢᱤᱫᱴᱟᱝ")]
SPEAKER = 7
SCALES = (0.333, 1.15, 0.333)
MAX_TAKES = 10


def ol_chiki(s):
    return re.sub(r"[^ᱚ-ᱽ]", "", unicodedata.normalize("NFC", s))


def main():
    cfg = json.loads((MDIR / "model" / "santali_piper_vits.onnx.json").read_text(encoding="utf-8"))
    sr, idm = cfg["audio"]["sample_rate"], cfg["phoneme_id_map"]
    sess = ort.InferenceSession(str(MDIR / "model" / "santali_piper_vits.onnx"), providers=["CPUExecutionProvider"])
    rec = sherpa_onnx.OfflineRecognizer.from_nemo_ctc(
        model=sys.argv[1], tokens=sys.argv[2], num_threads=4, sample_rate=16000, feature_dim=80,
        decoding_method="greedy_search")

    for name, hindi, text in PHRASES:
        ids = idm["^"] + [x for ch in santhali_to_ipa(text) for x in idm[ch] + idm["_"]] + idm["$"]
        feed = {"input": np.array([ids], np.int64), "input_lengths": np.array([len(ids)], np.int64),
                "scales": np.array(SCALES, np.float32), "sid": np.array([SPEAKER], np.int64)}
        for take in range(1, MAX_TAKES + 1):
            a = sess.run(None, feed)[0].squeeze()
            a = (a / (np.abs(a).max() + 1e-9) * 0.9).astype(np.float32)
            s = rec.create_stream()
            s.accept_waveform(sr, a)
            rec.decode_stream(s)
            heard = s.result.text.strip()
            if ol_chiki(heard) == ol_chiki(text):
                break
        else:
            raise SystemExit(f"{text}: no take out of {MAX_TAKES} was transcribed exactly; not saving")
        path = HERE / name
        sf.write(path, a, sr, subtype="PCM_16")

        # Verification: re-open with the stdlib parser and check for audible, non-empty speech.
        with wave.open(str(path)) as w:
            ok_fmt = (w.getcomptype(), w.getnchannels(), w.getsampwidth(), w.getframerate()) == ("NONE", 1, 2, sr)
            frames = w.getnframes()
            pcm = np.frombuffer(w.readframes(frames), dtype="<i2").astype(np.float32) / 32768
        f = int(sr * 0.02)
        rms = np.sqrt((pcm[: len(pcm) // f * f].reshape(-1, f) ** 2).mean(1))
        loud_ms = int((rms > 0.02).sum() * 20)
        print(f"{name}: {hindi} -> {text} | take {take} | ASR heard '{heard}' | {path.stat().st_size} B | "
              f"{sr} Hz mono 16-bit PCM={ok_fmt} | {frames / sr:.3f} s | peak {np.abs(pcm).max():.2f} | "
              f"frames above -34 dBFS: {loud_ms} ms")
        if not ok_fmt or frames == 0 or loud_ms < 200:
            raise SystemExit(f"{name}: failed verification")


if __name__ == "__main__":
    main()
