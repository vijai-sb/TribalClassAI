# IndicTrans2 hin_Deva → sat_Olck — verification and Android feasibility (2026-09-29)

IndicTrans2 is text → text. The app pipeline is: Hindi speech → Hindi ASR → Hindi text → IndicTrans2 →
Ol Chiki text → cached Santali WAV (pre-generated, not real-time TTS).

## Model
`hari31416/indictrans2-indic-indic-dist-320M-ONNX-int8` (ONNX export of `ai4bharat/indictrans2-indic-indic-dist-320M`),
downloaded to `model/` (not in the APK). Earlier copies in the HF cache had been deleted (empty `refs/main` only).
Weights: encoder 120 MB + decoder 203 MB (shared by `decoder_model.onnx` and `decoder_with_past_model.onnx`) ≈ 323 MB;
plus tokenizer JSONs 2 × 24 MB. fp32 variant: ≈ 1.28 GB (not downloaded).

## Verification (`verify_translation.py`, log `verify_log.txt`, data `verify_result.json`)
Desktop, onnxruntime 1.22.1, model repo's own `translate.py` with IndicProcessor, greedy decoding.

| Hindi | Actual output | Target token ids |
|---|---|---|
| किताब | `ᱯᱚᱛᱚᱵ ᱾` | 103129, 31428, 2 |
| एक | `ᱢᱤᱫᱴᱟᱝ ᱾` | 64583, 31428, 2 |

The word is exact; the model appends the Ol Chiki full stop ᱾ (U+1C7E). The app shows the output unchanged and
trims trailing punctuation only to match a WAV (agreed with the project owner).
Process memory: ≈ 740 MB RSS after loading (desktop, both decoder sessions load the 203 MB data file). ≈ 130–180 ms per word.

## Android: not practical for this prototype
- sherpa-onnx (Hindi ASR) bundles `libonnxruntime.so` 1.28.2 and links `OrtGetApiBase@VERS_1.28.2`. The ORT Android
  Java package is 1.28.0 or 1.30.0 on Maven and ships its own `libonnxruntime.so`; only one can be packaged, and
  Android's linker rejects the mismatched symbol version. Fixing it needs binary patching or an NDK build.
- RAM: ≥ 400 MB for translation on top of ≈ 200 MB for ASR; the test emulator (2.5 GB) had ~1.1 GB free.
- No Kotlin SentencePiece/IndicProcessor port.

So `RecordedIndicTrans2Repository` in the app returns the two outputs above, labelled in the UI as a recorded desktop
run. `IndicTrans2Repository` is the slot for an on-device implementation.
