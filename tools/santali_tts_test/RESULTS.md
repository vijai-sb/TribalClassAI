# Phase 9A — Santali TTS proof of concept: results

**Decision: FAIL. Do not integrate into Android.**
The model runs, is fast, and writes valid, playable WAVs, but an independent Santali recogniser
does not hear the intended words in any of 36 syntheses, and the model's licensing is doubtful.

## Model

| | |
|---|---|
| Model | `sat_piper_model.onnx` + `sat_piper_model.onnx.json` |
| Repository | Hugging Face `Ashraf01k/vernacular-pedagogy-santhali`, commit `f62ae7c9a9b83a452a970efee3ef443aff4a169c` (created 2026-09-07, 0 downloads) |
| Size | 63,516,051 bytes; SHA-256 `ae73d347…515e44` (matches the Hugging Face LFS record) |
| Architecture | Piper VITS, single speaker, 16 kHz, `phoneme_type: "text"` — input symbols are Ol Chiki letters (U+1C50–U+1C7D) plus punctuation, 68 symbols used |
| Runtime | ONNX Runtime (CPU). Inputs `input` (int64 ids), `input_lengths`, `scales` [noise, length, noise_w]; output float waveform |
| Santali / Ol Chiki input | Accepted: every character of both test strings is in the symbol map |
| Declared licence | MIT (model card only) |
| Published benchmark | README claims RTF 0.051–0.081 and 41–87 ms per command. No intelligibility, MOS or native-speaker evaluation published |

## Provenance and licence notes

From the model card and the linked GitHub project `AshrafGalaxy/Vernacular_Pedagogy` (created 2026-09-06, **no licence file**):

- Fine-tuned (warm start) from Piper's English `en_US/lessac/medium` checkpoint. That checkpoint was trained on the
  **Blizzard 2013 Lessac** data, whose licence limits use to non-commercial research and prohibits distributing the
  materials without written consent. A derivative released as "MIT" is therefore doubtful.
- Santali training audio: Hugging Face datasets `XKaab/ASR-santali_100hrs` and `XKaab/ASR-Santali_4hrs` — **no licence
  and no source information declared**. IndicVoices-R (CC-BY-4.0) and Common Voice are also listed in the fetch script.
- Training size is inconsistent across the project's own files: the notebook says ~500 clips / 25 epochs, the cloud
  script says 2,500 clips / 80 epochs. No training logs or evaluation are published.
- Could not verify: actual clips/hours used, speaker consent, final epoch count, any quality evaluation.

## Test

- Isolated environment: `tools/santali_tts_test/.venv` (Python 3.12.10, onnxruntime 1.22.1, numpy, soundfile,
  sherpa-onnx 1.13.8, psutil). Laptop CPU, 4 threads.
- Input: exactly the two existing phrase-pack strings, `ᱯᱚᱛᱚᱵ` and `ᱢᱤᱫᱴᱟᱝ`. No other Santali text was used.
- Encoding: standard Piper text voice, `^` + (letter, `_`)… + `$`; scales from the config (0.667, 1.0, 0.8).
- Commands:
  ```
  .venv\Scripts\python.exe synthesize.py
  .venv\Scripts\python.exe evaluate.py <IndicConformer sat model.int8.onnx> <tokens.txt>
  ```

## Output WAVs (`output/`)

| File | Text | Size | Format | Duration | Speech span | Clipping |
|---|---|---|---|---|---|---|
| `santali_book.wav` | ᱯᱚᱛᱚᱵ | 20,524 B | 16 kHz, mono, 16-bit PCM | 0.64 s | 0.50 s | none |
| `santali_one.wav` | ᱢᱤᱫᱴᱟᱝ | 50,732 B | 16 kHz, mono, 16-bit PCM | 1.58 s | 1.16 s | none |

Both parse with Python's standard `wave` module and with libsndfile, so they are valid, playable WAV files.

## Speed and memory

| | |
|---|---|
| Model load | 2,332 ms |
| Synthesis, ᱯᱚᱛᱚᱵ | median 34 ms (24–45) over 5 runs, RTF 0.053 |
| Synthesis, ᱢᱤᱫᱴᱟᱝ | median 55 ms (38–90) over 5 runs, RTF 0.035 |
| Memory | +95 MB RSS after load; 173 MB process peak |

Speed would be fine for the prototype.

## Intelligibility

I cannot listen to audio, so intelligibility was checked with an **ASR proxy**: AI4Bharat IndicConformer Santali
(sherpa-onnx, int8 CTC) transcribes each clip and the result is compared with the intended Ol Chiki letters
(character error rate, CER). The same recogniser previously transcribed a real Santali TTS voice (Bhashini IITM, from a
reference repo) at a median CER of 0.10, so it does recognise Santali speech. The proxy is not a native-speaker judgement.

| Test | Result |
|---|---|
| Saved outputs | ᱯᱚᱛᱚᱵ heard as `ᱠᱷᱫ ᱠᱚ` (CER 1.00); ᱢᱤᱫᱴᱟᱝ heard as `ᱥ` (CER 1.00) |
| 10 fresh syntheses per phrase | 0/20 exact; median CER 1.00; transcripts differ randomly run to run (e.g. `ᱪᱠᱟ`, `ᱚᱠᱛᱚ`, `ᱛᱚᱦᱚᱵ`; ᱢᱤᱫᱴᱟᱝ mostly `ᱦᱩᱸ`/`ᱦᱮᱸ`) |
| 4 alternative encodings × 2 scale settings (16 clips) | none recognised; deterministic settings give ~0.4 s for ᱢᱤᱫᱴᱟᱝ, very short for six letters |
| Repository's own samples (`repo_samples/`) | also not recognised (`ᱥᱤᱡᱩ`, `ᱴᱫ`, nothing, `ᱦᱚᱢ`); their intended text is not published |

The audio is strongly voiced (75–100% of frames have a clear pitch, similar to the repo's samples), so it produces
voice-like sound, but there is no evidence that it produces the intended Santali words.

## Problems encountered

- Licensing/provenance of the model is doubtful (see above).
- The project's Android code converts Ol Chiki to IPA before synthesis, but the published config contains no IPA
  symbols; its IPA output would not map to model ids. I followed the config (character input). Other encodings were
  tried and did not help.
- Output is random run to run (Piper sampling), and the recogniser hears different fragments each time.

## Criteria

| Criterion | Result |
|---|---|
| 1. Accepts Ol Chiki input | PASS |
| 2. Produces valid audio | PASS |
| 3. Audio is playable | PASS (valid 16-bit PCM WAV) |
| 4. Speech reasonably recognisable | **FAIL** by ASR proxy (0/36 recognised); human listening not done |
| 5. Fast enough | PASS (34–55 ms per word) |

## Recommendation

Do not integrate this model. Before closing the question entirely, a Santali speaker could listen to
`output/santali_book.wav` and `output/santali_one.wav`: if they clearly hear ᱯᱚᱛᱚᱵ and ᱢᱤᱫᱴᱟᱝ, the ASR proxy is wrong
and the licensing question becomes the only blocker. Otherwise, the next candidate is the official AI4Bharat
Indic Parler-TTS (Apache-2.0, gated — needs a Hugging Face login and accepted terms), or recordings by a Santali speaker
for the fixed phrase pack, which the app's existing `SantaliRecordings` registry already supports.
