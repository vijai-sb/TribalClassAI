"""Santali ASR proxy check (AI4Bharat IndicConformer sat, via sherpa-onnx) on given WAV files.

A file passes if the transcript's Ol Chiki letters equal the intended text (spaces ignored); CER is reported
so a candidate can be compared with the currently shipped file. A proxy for intelligibility, not proof.

Usage: ..\\.venv\\Scripts\\python.exe asr_check.py <sat model.int8.onnx> <tokens.txt> <file.wav>=<Ol Chiki> ...
"""
import sys
import wave

import numpy as np
import sherpa_onnx

from generate_prototype_audio import ol_chiki


def cer(heard, text):
    a, b = ol_chiki(heard), ol_chiki(text)
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        p, d[0] = d[0], i
        for j, cb in enumerate(b, 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (ca != cb))
    return d[-1] / max(len(b), 1)


def main():
    rec = sherpa_onnx.OfflineRecognizer.from_nemo_ctc(
        model=sys.argv[1], tokens=sys.argv[2], num_threads=4, sample_rate=16000, feature_dim=80,
        decoding_method="greedy_search")
    for arg in sys.argv[3:]:
        path, text = arg.split("=", 1)
        with wave.open(path) as w:
            x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768
            sr = w.getframerate()
        s = rec.create_stream()
        s.accept_waveform(sr, x)
        rec.decode_stream(s)
        heard = s.result.text.strip()
        print(f"{path} | heard '{heard}' | exact {ol_chiki(heard) == ol_chiki(text)} | CER {cer(heard, text):.2f}")


if __name__ == "__main__":
    main()
