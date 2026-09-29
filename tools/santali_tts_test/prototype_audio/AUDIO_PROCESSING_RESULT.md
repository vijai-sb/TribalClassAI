# Prototype audio: loudness processing and sentence audio (2026-09-29)

Pre-generated Santali speech (TTS model) — not real-time TTS, not reviewed by a Santali speaker.
Processing changes loudness and tonal balance only; it does not improve pronunciation.

## Why the old clips sounded quiet / muffled
- Already peak-normalised (−0.9 dBFS), so level could not simply be raised; high crest factor (16–21 dB).
- DC offset (+0.024 / +0.012 FS) and sub-80 Hz energy that phone speakers can't reproduce.
- TTS output is band-limited: relative to 300–1000 Hz, 2–3 kHz is −37 dB (book) / −19 dB (one), >4 kHz ≤ −45 dB.
- On the emulator, media volume was 5/15 (the largest factor; since set to 15).

## Processing (`process_audio.py`, log `process_log.txt`)
From the original takes (`*_nopad.wav`): 80 Hz high-pass and +4 dB presence peak at 2.5 kHz (both zero phase),
make-up gain with a smooth look-ahead limiter (ceiling −1 dBFS, ≤ 6 dB gain reduction, no hard clipping),
5 ms edge fades, same 300/200 ms padding as `pad_audio.py`. 22,050 Hz mono 16-bit PCM; duration unchanged.
Previous app versions remain here as `santali_book.wav` / `santali_one.wav`.

| Clip | Loudness old → new | Speech RMS (after 80 Hz HPF) old → new | Peak old → new | DC old → new | Duration | Size |
|---|---|---|---|---|---|---|
| santali_book | −16.6 → −15.1 LUFS | −15.6 → −14.3 dBFS | −0.92 → −1.00 dBFS | +0.024 → 0 | 1.266 s | 55,886 B |
| santali_one | −20.0 → −17.9 LUFS | −19.1 → −17.4 dBFS | −0.92 → −1.00 dBFS | +0.012 → 0 | 1.661 s | 73,294 B |

Clipped samples: 0 in all files. Santali ASR proxy (IndicConformer sat): book old `ᱯᱨᱚᱛᱚᱵ` → new `ᱯᱚᱛᱚᱵ` (exact);
one old `ᱢᱮᱴᱟ` → new `ᱢᱤᱫᱴᱟ` (closer, final ᱝ missed). The unpadded original takes are heard exactly; the padding
added earlier already worsened the proxy result.

## Sentence audio (`generate_sentence_audio.py`, log `generate_sentence_log.txt`)
अपना नाम लिखो। → ᱟᱢᱟᱜ ᱧᱩᱛᱩᱢ ᱚᱞ ᱢᱮ (IndicTrans2; see tools/indictrans2_test/verify_sentences_log.txt).
Same voice/settings as the word clips; 0 of 20 takes transcribed exactly (the ending ᱚᱞ ᱢᱮ is garbled).
**No audio added.** The app shows the sentence as text only.
