# Santali audio prototype — integration result

**What this is:** pre-generated Santali speech audio generated using a Santali TTS model and bundled for offline
playback. It is not real-time or on-device TTS: nothing is synthesized on the phone.

**Status:** prototype demonstration only. The clips have **not** been checked by a Santali speaker (the Phase 9C human
listening result is still pending), and the model's training-data licence and Lessac warm-start questions remain
unverified (see `../phase9c/HUMAN_VALIDATION_RESULT.md`). The app labels the audio "Pre-generated Santali speech
(TTS model)", next to the existing "Machine-generated · not yet reviewed" label on the text.

## Model

`kaushalkrishnax/santali-piper-vits`, Hugging Face commit `ba883eed`, file `model/santali_piper_vits.onnx`
(SHA-256 `ff3beb17…c65ac`). Piper VITS, speaker 7, settings noise_scale 0.333 / length_scale 1.15 / noise_w 0.333,
Ol Chiki → `santhali_to_ipa()` → model symbols. Same setup as Phase 9C.

Script: `generate_prototype_audio.py` (log: `generate_log.txt`). It keeps the first of up to 10 takes that the
independent Santali ASR (AI4Bharat IndicConformer) transcribes exactly — a filter, not proof of correctness.

## Phrases generated

Only the Santali entries already in `OfflinePhrasePack.kt`; no new translations.

| Hindi | Santali | File | Take kept | ASR heard |
|---|---|---|---|---|
| किताब | ᱯᱚᱛᱚᱵ | `santali_book.wav` | 5 of 10 | ᱯᱚᱛᱚᱵ |
| एक | ᱢᱤᱫᱴᱟᱝ | `santali_one.wav` | 1 of 10 | ᱢᱤᱫᱴᱟᱝ |

## WAV files

| File | Size | Format | Duration | Peak | Audible (frames above −34 dBFS) | SHA-256 |
|---|---|---|---|---|---|---|
| `santali_book.wav` | 33,836 B | 22,050 Hz, mono, 16-bit PCM (uncompressed) | 0.766 s | 0.90 | 760 ms | `6d0700d5…b6ae81` |
| `santali_one.wav` | 51,244 B | 22,050 Hz, mono, 16-bit PCM (uncompressed) | 1.161 s | 0.90 | 540 ms | `85b367f0…055ed1` |

Both open with Python's standard `wave` parser, are non-empty, and contain audible signal. The copies in
`app/src/main/res/raw/` have identical hashes.

## Android integration

- Files copied to `app/src/main/res/raw/santali_book.wav` and `app/src/main/res/raw/santali_one.wav`.
- Registered in the existing `SantaliRecordings` registry; the existing `SantaliAudioRepository` (Hindi + exact Ol Chiki
  match) and `SantaliAudioPlayer` (MediaPlayer) are unchanged.
- A new `AudioSourceKind.PRE_GENERATED_TTS` value was added so the UI does not show TTS output as "Pre-recorded" (the
  only existing kind meant a recording of a person). Its label: "Pre-generated Santali speech (TTS model)".

## Build result

`.\gradlew.bat assembleDebug`: **BUILD SUCCESSFUL**, no compiler errors or warnings.
`aapt2 dump resources` on the APK lists `raw/santali_book` (0x7f0a0000) and `raw/santali_one` (0x7f0a0001); the APK
entries `res/raw/santali_book.wav` (33,836 B) and `res/raw/santali_one.wav` (51,244 B) match the source files.

## Device test (Android 16 API 36 emulator)

| Step | ᱯᱚᱛᱚᱵ (किताब) | ᱢᱤᱫᱴᱟᱝ (एक) |
|---|---|---|
| Translate shows the Ol Chiki text | yes | yes |
| Play Audio enabled, label "Pre-generated Santali speech (TTS model)" | yes | yes |
| Press Play → Android audio service | MediaPlayer `event:started`, 22,050 Hz mono, routed to device 2; `event:stopped` and released 1.6 s later | `event:started`, 22,050 Hz mono; stopped and released 1.3 s later |
| Press Play then Stop after 0.25 s | — | stopped 0.29 s after start (clip is 1.16 s); button back to "Play Audio" |
| Crashes | none | none |

Playback was confirmed from Android's audio service logs. The emulator's sound was not listened to (this environment
cannot hear audio), so a person should press Play on a device and listen.

## Exact files changed

Android project (compared against checksums taken just before this task):

| File | Change |
|---|---|
| `app/src/main/res/raw/santali_book.wav` | new |
| `app/src/main/res/raw/santali_one.wav` | new |
| `app/src/main/java/com/tribalclass/ai/data/SantaliRecordings.kt` | two clip entries + prototype credit and doc comment |
| `app/src/main/java/com/tribalclass/ai/data/SantaliAudioClip.kt` | added `AudioSourceKind.PRE_GENERATED_TTS` |
| `app/src/main/java/com/tribalclass/ai/ui/teacher/TeacherModeScreen.kt` | one line: label for the new kind |
| `app/src/main/res/values/strings.xml` | one string: `audio_kind_pre_generated_tts` |

Not changed: Hindi ASR, translation logic and phrase pack, worksheets, lessons, Home, navigation,
`SantaliAudioRepository.kt`, `SantaliAudioPlayer.kt`, Gradle files, manifest.

Research tools (`tools/santali_tts_test/prototype_audio/`): `generate_prototype_audio.py`, `generate_log.txt`,
`santali_book.wav`, `santali_one.wav`, this file. Phase 9A/9C files were not touched.
