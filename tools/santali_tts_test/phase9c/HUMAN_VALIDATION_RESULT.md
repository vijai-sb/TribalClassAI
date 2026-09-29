# Human validation result — Santali TTS candidate

STATUS: WAITING FOR HUMAN SANTALI SPEAKER

Nothing below is a pass or fail decision. The model is not approved.

## Model

| | |
|---|---|
| Model | `kaushalkrishnax/santali-piper-vits` (Piper VITS, 80 female voices, 22.05 kHz) |
| Revision | Hugging Face commit `ba883eed38eed0111589a3796c20c890b1d0c35b` |
| File tested | `model/santali_piper_vits.onnx`, 77,148,263 bytes (73.6 MiB), SHA-256 `ff3beb17a5252344dd8246ea7365fca258d6a400ce76f94a796929c15afc65ac` |
| Input pipeline | Ol Chiki → bundled `santhali_to_ipa()` → model symbols |
| Speaker tested | speaker id 7 |
| Settings | noise_scale 0.333, length_scale 1.15, noise_w 0.333; output peak-normalised to 0.9 |

## Intended phrases and audio files (`human_validation/`)

| Clip | Intended text | File | Format | Duration | Size | SHA-256 (first 16) |
|---|---|---|---|---|---|---|
| 1 | ᱯᱚᱛᱚᱵ | `santali_book_best_spk7_calmer.wav` | 22,050 Hz, mono, 16-bit PCM | 1.115 s | 49,196 B | `a35334855ada891a` |
| 2 | ᱢᱤᱫᱴᱟᱝ | `santali_one_best_spk7_calmer.wav` | 22,050 Hz, mono, 16-bit PCM | 1.045 s | 46,124 B | `ca0e09553c3c8926` |

Both files parse with Python's standard `wave` module and libsndfile (valid, uncompressed WAV). They are exact copies of
the files in `output_kaushal/` (identical hashes). They were not regenerated.

## Automated ASR results (proxy only — not proof of intelligibility)

Recogniser: AI4Bharat IndicConformer Santali (sherpa-onnx, int8 CTC). It is probably trained on the same IndicVoices
speech as this TTS, which may flatter the results.

| Test | ᱯᱚᱛᱚᱵ | ᱢᱤᱫᱴᱟᱝ |
|---|---|---|
| These two exact clips | heard exactly | heard exactly |
| Speaker 7, same settings, 20 fresh samples | 11/20 exact (misses mostly ᱯᱚᱛᱚ, ᱯᱛᱚᱵ, ᱡᱚᱛᱚᱵ) | 19/20 exact (1 × ᱢᱮᱛᱟᱝ) |
| All 80 voices, same settings, 4 samples each | 78/320 exact (24%) | 168/320 exact (52%) |

Note: the two clips were chosen *because* the recogniser heard them correctly, so they are the best-case takes.

## Licensing and provenance status

No legal conclusions are made here.

| Item | Finding | Status |
|---|---|---|
| Model licence | Model card metadata says Apache-2.0 | Stated by author; unverified whether the author could grant it |
| Training code | Piper training pipeline; model card links `OHF-Voice/piper1-gpl` (GPL-licensed code) | Effect on model weights unverified |
| Training dataset | `XKaab/ASR-santali_100hrs` (20.05 h, 10,348 utterances, 80 female speakers selected). Dataset card has **no licence field** and no source statement | Unverified |
| Training-data origin | Dataset columns (`verbatim`, `normalized`, `scenario`, `task_name`, `verification_report`, `unsanitized_verbatim`, speaker metadata) and the Read/Conversation/Extempore mix match AI4Bharat IndicVoices, which is CC-BY-4.0 and gated behind accepted terms | Unverified — resemblance only, not confirmed |
| Trained from scratch? | **No, at least partly warm-started.** The epoch-50 checkpoint's stored hyper-parameters contain `vocoder_warmstart_ckpt = /kaggle/working/santali_piper/base_model/en_US-lessac-medium.ckpt`. `warmstart_ckpt` appears empty (no value stored), but this was read from raw bytes, not by loading the checkpoint | Vocoder warm start: found in checkpoint. Full-model warm start: unverified |
| Base checkpoint | Piper `en_US-lessac-medium` (rhasspy/piper-voices). Its model card points to the Blizzard 2013 Lessac dataset licence, whose terms restrict use to non-commercial research and restrict distribution of the materials | Whether those terms extend to a model fine-tuned from this checkpoint: unverified |
| Speaker consent / attribution | No attribution to the original speech providers is given in the model repository | Unverified |

How the warm-start finding was obtained: `inspect_ckpt_hparams.py` read only the zip directory and `data.pkl` of
`model/santali_piper_vits_epoch50.ckpt` via HTTP range requests and listed its text strings (no unpickling);
output in `ckpt_hparams_log.txt`.

## Still needs human confirmation

1. A Santali speaker listens to both clips and answers the questions in `human_validation/HUMAN_VALIDATION.md`.
2. Whether this synthetic audio is acceptable for classroom use with young children.
3. From the model author (or a licensing reviewer): the true source and licence of `XKaab/ASR-santali_100hrs`, whether
   the Lessac warm start is compatible with the intended use, and whether any other base checkpoint was used.

Only after (1) and (3) should this file be changed from WAITING to a decision.
