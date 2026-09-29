# Phase 9C Results

Date: 2026-09-29. Research and tests ran only under `tools/santali_tts_test/`; the Android project was not modified.

## Executive Summary

No sufficiently verified lightweight Santali TTS model was found — but one candidate is **promising and needs human
listening**: `kaushalkrishnax/santali-piper-vits` (Piper VITS, 73.6 MB ONNX, 22.05 kHz, 80 female voices, Ol Chiki input
via a bundled G2P script). On the laptop CPU it synthesizes a word in ~56–71 ms (4 threads) / ~148 ms (1 thread). With
calmer sampling settings and its best voice (speaker 7), an independent Santali recogniser heard **ᱢᱤᱫᱴᱟᱝ exactly in 19/20**
samples and **ᱯᱚᱛᱚᱵ exactly in 11/20** (most misses were near: ᱯᱚᱛᱚ, ᱯᱛᱚᱵ). This is a large improvement over the Phase 9A
model (0/36). It is not a PASS because no human has listened, the recogniser is only a proxy (and probably shares training
data with the TTS), the training dataset carries no licence label, and the base checkpoint is not documented.

Every other candidate either does not support Santali, is far too large for a 2 GB phone, is API-only, or has no
published weights.

## Candidate Comparison

| Model | Santali | Ol Chiki | Size | Runtime | CPU Speed | License | Provenance | Quality | Decision |
| ----- | ------- | -------- | ---- | ------- | --------- | ------- | ---------- | ------- | -------- |
| kaushalkrishnax/santali-piper-vits | Yes (sat, 20 h Santali speech) | Yes, via bundled `santhali_to_ipa()` G2P | 73.6 MB ONNX | ONNX Runtime (Piper VITS) | 56–71 ms/word (4 thr), 148 ms (1 thr), laptop. Android CPU latency not verified | Apache-2.0 (model card) | Data: XKaab re-upload, no licence label (schema matches AI4Bharat IndicVoices, CC-BY-4.0); base checkpoint not stated | ASR proxy: best voice 19/20 and 11/20 exact; all voices 52% / 24% (calmer settings) | PROMISING — HUMAN LISTENING REQUIRED |
| Ashraf01k/vernacular-pedagogy-santhali (Phase 9A) | Claimed | Yes (character input) | 63.5 MB ONNX | ONNX Runtime (Piper VITS) | 34–55 ms/word, laptop | MIT (card) | Fine-tuned from Piper en_US Lessac (Blizzard 2013, research-only); unlicensed XKaab data | ASR proxy: 0/36 recognised | FAIL — QUALITY |
| ai4bharat/indic-parler-tts (baseline) | Yes, listed as officially supported; absent from its evaluation table | Not stated on card | 0.94B params (~3.6 GB repo) | PyTorch + parler-tts | Not measured (gated; no HF token here). Android CPU latency not verified | Apache-2.0 | Official AI4Bharat | No Santali samples or scores published; not tested | FAIL — TOO LARGE/SLOW (for on-device; usable offline on a PC for pre-generation) |
| Meta MMS TTS (`facebook/mms-tts-sat`) | No — `sat` absent from the MMS TTS language list (~1,350 languages); no HF repo | — | — | — | — | CC-BY-NC-4.0 (MMS TTS) | — | — | FAIL — NOT ACTUALLY SANTALI |
| AI4Bharat Indic-TTS (FastPitch + HiFi-GAN) | No — 13 languages, no Santali checkpoint in release | — | — | PyTorch/Coqui | — | MIT | Official | — | FAIL — NOT ACTUALLY SANTALI |
| IITM `smtiitm/Fastspeech2_HS` (main + New-Models) | No — no Santali in language table or model folders | — | — | PyTorch | — | CC-BY-4.0 | Official IITM | — | FAIL — NOT ACTUALLY SANTALI |
| Bhashini (IITM) Santali TTS | Yes, as a hosted service (earlier session evaluated its clips from another team's repo: median CER 0.10) | Yes (service input) | No downloadable model found | Online API | — | Bhashini platform terms (registration) | Official, but not downloadable | Good by ASR proxy (earlier session) | FAIL — NOT PRACTICAL FOR ANDROID (API-only, not offline) |
| mondal-anindita/santaliTTS_Inference (Glow-TTS + HiFi-GAN, IIIT Hyderabad researcher) | Claimed | Unknown | Unknown | PyTorch | — | No licence file | Weights only via a SharePoint link; no data documentation | No samples | UNKNOWN — INSUFFICIENT EVIDENCE |
| Santali-AI/Open-SAIR- (VITS engine code) | Claimed | Claimed | No weights published | PyTorch (server/GPU) | — | Apache-2.0 (code) | Framework code only | None | UNKNOWN — INSUFFICIENT EVIDENCE |
| k2-fsa/OmniVoice (zero-shot, 646 languages incl. `sat`) | Tag only; no Santali evaluation seen | Unknown | 0.61B params + audio tokenizer (~3.1 GB repo) | PyTorch | Not measured | Not stated on card | Qwen3-0.6B base | Not tested | FAIL — TOO LARGE/SLOW |
| bodhan-ai/indic-speak (+ adidsh int8/GGUF re-upload) | Tagged `sat` | Unknown | 3.3B params (Llama-3.2-3B base) | PyTorch / GGUF | Not measured | Custom "other" licence; gated | Re-upload by a third party | Not tested | FAIL — TOO LARGE/SLOW |
| rumik-ai/rumik-oss-1 | Tagged `sat` | Unknown | 3.4B params | PyTorch | Not measured | CC-BY-NC-4.0 | — | Not tested | FAIL — TOO LARGE/SLOW |

## Detailed Findings

### 1. kaushalkrishnax/santali-piper-vits — PROMISING — HUMAN LISTENING REQUIRED
- **Source:** Hugging Face, commit `ba883eed38eed0111589a3796c20c890b1d0c35b` (created 2026-09-26). ONNX SHA-256
  `ff3beb17…c65ac` (matches the Hugging Face LFS record).
- **Architecture:** Piper VITS, 80 speakers (`sid` input), 22,050 Hz, 168 IPA-style symbols, Piper v1.5/1.6.1, 50 epochs
  on 2× T4. Inputs: `input`, `input_lengths`, `scales`, `sid`.
- **Language/script:** Santali; Ol Chiki text is converted by the bundled `santhali_phonemizer.py` (`santhali_to_ipa`,
  reviewed: pure string rules, no I/O). ᱯᱚᱛᱚᱵ → `pɔtɔb`, ᱢᱤᱫᱴᱟᱝ → `midʈaŋ`; all symbols are in the model's map. The same
  rules would need porting to Kotlin for on-device synthesis (≈250 lines, table-driven).
- **Size/runtime:** 73.6 MB ONNX; runs on ONNX Runtime CPU. Load 2.07 s, +109 MB RSS (laptop). The repo also has
  881.9 MB training checkpoints (not needed) and a 68.2 MB "android" tarball (not inspected).
- **Measured (laptop CPU):** synthesis median 71 ms (ᱯᱚᱛᱚᱵ, 1.14 s audio) and 56 ms (ᱢᱤᱫᱴᱟᱝ, 1.06 s), RTF 0.05–0.06 with
  4 threads; 148 ms with 1 thread. **Android CPU latency not verified.** Raw output is quiet (peak 0.06–0.09) and needs
  normalisation.
- **Licence/provenance:** model card Apache-2.0. Training data `XKaab/ASR-santali_100hrs` (20.05 h, 10,348 utterances,
  80 female speakers) declares **no licence and no source**; its column schema and speaker/task fields match AI4Bharat
  IndicVoices (CC-BY-4.0, attribution required), which strongly suggests an unlabelled re-upload — inference, not proof.
  The training config does not state whether a base checkpoint (e.g. an English Piper voice with its own licence) was used.
- **Quality evidence (ASR proxy, AI4Bharat IndicConformer Santali):**
  - default settings (0.667, 1.0, 0.8), 80 voices × 4: ᱯᱚᱛᱚᱵ 22/320 (7%), ᱢᱤᱫᱴᱟᱝ 78/320 (24%) exact;
  - calmer settings (0.333, 1.15, 0.333), 80 voices × 4: ᱯᱚᱛᱚᱵ 78/320 (24%), ᱢᱤᱫᱴᱟᱝ 168/320 (52%) exact; 5 voices never matched;
  - speaker 7, calmer, 20 samples each: ᱯᱚᱛᱚᱵ 11/20, ᱢᱤᱫᱴᱟᱝ 19/20 exact.
- **Limitations:** the recogniser is not a listener and was probably trained on the same IndicVoices speech, which may
  flatter these voices; results vary by voice and random sampling; only two words were tested; human listening not done
  (this environment cannot play audio to a person).
- **Samples for listening** (`phase9c/output_kaushal/`, all 22.05 kHz mono 16-bit):
  `santali_book_best_spk7_calmer.wav` (1.11 s), `santali_one_best_spk7_calmer.wav` (1.04 s) — both heard exactly by the ASR;
  `santali_book_spk0.wav`, `santali_one_spk0.wav`, `…_spk8.wav`, `…_spk40.wav` — default settings, mixed ASR results.

### 2. Ashraf01k/vernacular-pedagogy-santhali — FAIL — QUALITY
See `RESULTS.md` (Phase 9A). Valid, fast audio but 0/36 recognised; licensing doubtful (Lessac base, unlicensed data).

### 3. ai4bharat/indic-parler-tts — baseline, FAIL — TOO LARGE/SLOW for on-device
0.94B parameters, Apache-2.0, official. Card lists Santali among officially supported languages but gives no Santali
evaluation or speaker list, and no input-script statement. Gated (Hugging Face login + accepted terms), so not
downloaded or tested here. Suitable only for offline pre-generation on a PC.

### 4. Meta MMS TTS — FAIL — NOT ACTUALLY SANTALI
`sat` is not in the official MMS TTS language list, and no `facebook/mms-tts-sat` repository exists (Hub search: 0).

### 5. AI4Bharat Indic-TTS and IITM FastSpeech2_HS — FAIL — NOT ACTUALLY SANTALI
Indic-TTS: 13 languages (release assets as/bn/brx/gu/hi/kn/ml/mni/mr/or/pa/raj/ta/te/en). IITM FS2_HS: no Santali in the
language table, `main`, or `New-Models` folders.

### 6. Bhashini Santali TTS — FAIL — NOT PRACTICAL FOR ANDROID
A Santali voice exists as a Bhashini service (the earlier session measured such clips, taken from another team's repo, at
a median CER of 0.10). No downloadable checkpoint was found; access is through Bhashini's online platform and its terms,
so it cannot run offline. Its clips from other projects must not be reused.

### 7. Other Santali repositories — UNKNOWN — INSUFFICIENT EVIDENCE
`mondal-anindita/santaliTTS_Inference`: Glow-TTS/HiFi-GAN inference code; weights only on SharePoint; no licence.
`Santali-AI/Open-SAIR-`: framework code with a VITS engine; no trained weights published.

### 8. Large multilingual models — FAIL — TOO LARGE/SLOW
OmniVoice (0.61B), indic-speak (3.3B, custom licence), rumik-oss-1 (3.4B, non-commercial): far beyond a 2 GB-RAM phone;
none has published Santali evaluation.

## Recommended Technical Path

No sufficiently verified lightweight Santali TTS model was found.

**Next step (before any integration):** a Santali speaker listens to the six `phase9c/output_kaushal/` files and says
whether ᱯᱚᱛᱚᱵ and ᱢᱤᱫᱴᱟᱝ are clear. In parallel, confirm the training-data licence with the model author (is XKaab the
IndicVoices corpus, and was a base checkpoint used?).

**Prototype path — pre-generated audio, no on-device TTS:**

```
TTS on a PC (kaushal Piper voice if approved by a listener, else Indic Parler-TTS)
  ↓
Santali text from the phrase pack (ᱯᱚᱛᱚᱵ, ᱢᱤᱫᱴᱟᱝ)
  ↓
Generate several takes, keep only takes a Santali speaker approves
  ↓
Store the approved WAV/OGG files in app/src/main/res/raw/
  ↓
Register them in SantaliRecordings (existing registry)
  ↓
Existing SantaliAudioRepository → existing SantaliAudioPlayer → Android speaker
```

This needs no new Android runtime or model and fits the existing audio layer. The kaushal Piper voice would make
pre-generation cheap (tens of milliseconds per word on a laptop); Indic Parler-TTS remains the heavier alternative.
Because the existing UI labels audio as "Pre-recorded Santali audio", machine-generated clips would need their own label
(the `AudioSourceKind` enum was designed for this) — a decision for Phase 9B.

On-device synthesis with the kaushal voice is technically plausible later (73.6 MB model, ONNX Runtime is already in the
app through sherpa-onnx, G2P is small), but its Android latency and memory are unmeasured and its quality is unverified.

Not started: Android integration. Awaiting approval.
