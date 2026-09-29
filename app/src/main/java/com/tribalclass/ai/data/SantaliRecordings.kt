package com.tribalclass.ai.data

import com.tribalclass.ai.R

/**
 * Registry of bundled Santali audio clips.
 *
 * The current clips are prototype audio: pre-generated Santali speech audio generated using a Santali
 * TTS model and bundled for offline playback (see tools/santali_tts_test/prototype_audio/). They have
 * not been checked by a Santali speaker, and the model's training-data licence is unverified.
 *
 * To add a clip:
 *  1. Put the file in app/src/main/res/raw/ (lowercase, digits, underscores).
 *  2. Add an entry here with the exact Ol Chiki text spoken in it, the right [AudioSourceKind],
 *     and a credit line saying where it came from.
 */
object SantaliRecordings {
    private const val PROTOTYPE_TTS_CREDIT =
        "Pre-generated with kaushalkrishnax/santali-piper-vits (commit ba883eed), speaker 7; " +
            "prototype only, not reviewed by a Santali speaker, training-data licence unverified"

    val clips: List<SantaliAudioClip> = listOf(
        SantaliAudioClip(
            hindi = "किताब",
            santaliOlChiki = "ᱯᱚᱛᱚᱵ",
            rawResId = R.raw.santali_book,
            kind = AudioSourceKind.PRE_GENERATED_TTS,
            credit = PROTOTYPE_TTS_CREDIT,
        ),
        SantaliAudioClip(
            hindi = "एक",
            santaliOlChiki = "ᱢᱤᱫᱴᱟᱝ",
            rawResId = R.raw.santali_one,
            kind = AudioSourceKind.PRE_GENERATED_TTS,
            credit = PROTOTYPE_TTS_CREDIT,
        ),
        // Sentences: IndicTrans2 output from RecordedIndicTrans2Repository (text without the final ᱾/?),
        // and a take the Santali ASR transcribed exactly, checked again on this processed file.
        SantaliAudioClip(
            hindi = "बहुत अच्छा।",
            santaliOlChiki = "ᱟᱹᱰᱤ ᱱᱟᱯᱟᱭ",
            rawResId = R.raw.santali_very_good,
            kind = AudioSourceKind.PRE_GENERATED_TTS,
            credit = PROTOTYPE_TTS_CREDIT,
        ),
        SantaliAudioClip(
            hindi = "तुम्हारा नाम क्या है?",
            santaliOlChiki = "ᱟᱢᱟᱜ ᱧᱩᱛᱩᱢ ᱪᱮᱫ",
            rawResId = R.raw.santali_what_is_your_name,
            kind = AudioSourceKind.PRE_GENERATED_TTS,
            credit = PROTOTYPE_TTS_CREDIT,
        ),
    )
}
