package com.tribalclass.ai.data

/**
 * IndicTrans2 Hindi → Santali (hin_Deva → sat_Olck) text-to-text translation for the
 * "Hindi → Santali Audio" pipeline: Hindi ASR text in, Ol Chiki text out. It never handles audio.
 *
 * An on-device implementation (ONNX Runtime) would implement this interface. It is not in the app yet:
 * the ONNX Runtime library that sherpa-onnx bundles for Hindi ASR (1.28.2) can't be shared with the
 * ONNX Runtime Android Java package, and the INT8 model needs several hundred MB of RAM (see
 * tools/indictrans2_test/). Until then, [RecordedIndicTrans2Repository] is used.
 */
interface IndicTrans2Repository {
    /** Where this repository's output comes from, so the UI can say it plainly. */
    val provenance: IndicTrans2Provenance

    /** Returns IndicTrans2's output for [hindi], or null if it has none. Never invents text. */
    fun translate(hindi: String): IndicTrans2Result?

    /** Hindi phrases this repository can translate, for demo/test buttons. Empty if open-ended. */
    val knownPhrases: List<String> get() = emptyList()
}

enum class IndicTrans2Provenance {
    /** Translated on this device by the IndicTrans2 model. */
    ON_DEVICE,

    /** Output recorded from an IndicTrans2 run on a desktop computer; nothing is translated on the device. */
    RECORDED_DESKTOP_RUN,
}

data class IndicTrans2Result(
    val hindi: String,
    /** The model's decoded output, unchanged (IndicTrans2 ends it with the Ol Chiki full stop ᱾). */
    val rawOutput: String,
    /** Greedy-decoded target token ids, kept so the recorded output can be traced to the model run. */
    val targetTokenIds: List<Int>,
    val provenance: IndicTrans2Provenance,
) {
    /**
     * [rawOutput] without trailing whitespace and sentence-end punctuation (Ol Chiki ᱾ ᱿, Devanagari
     * danda, ASCII). Used only to match a bundled clip, which speaks the word without punctuation.
     */
    val olChikiForAudio: String
        get() = rawOutput.trimEnd { it.isWhitespace() || it in TRAILING_PUNCTUATION }

    /** This result as a [TranslationEntry], so the existing [SantaliAudioRepository] can match it. */
    fun toTranslationEntry(): TranslationEntry = TranslationEntry(
        hindi = hindi,
        santaliOlChiki = olChikiForAudio,
        status = TranslationStatus.MODEL_GENERATED_UNREVIEWED,
        source = "IndicTrans2 indic-indic-dist-320M ($provenance)",
    )

    private companion object {
        const val TRAILING_PUNCTUATION = "᱾᱿।॥.!?"
    }
}

/**
 * Outputs recorded from IndicTrans2 indic-indic-dist-320M, ONNX INT8
 * (hari31416/indictrans2-indic-indic-dist-320M-ONNX-int8), greedy decoding, hin_Deva → sat_Olck,
 * run on a desktop with the model repo's own translate.py. Logs and scripts in tools/indictrans2_test/:
 * verify_log.txt (words), verify_sentences_log.txt and verify_candidates_log.txt (sentences).
 *
 * Only phrases that passed verification are listed: identical output across repeated greedy runs,
 * beam-4 decoding, and the Hindi with and without its final punctuation; Ol Chiki only; and a
 * back-translation that keeps the meaning. Not the offline phrase pack; not used by the Translate button.
 *
 * Matching is exact after [PhrasePackTranslationRepository.normalize]. The Hindi ASR emits no final
 * punctuation, so a sentence is also found by its text without the final "।"/"?" - but only where the
 * model was checked to give the same output for that form ([Recorded.sameWithoutFinalPunctuation]).
 * Nothing else is stripped, so "किताब खोलो" can never match "किताब".
 */
class RecordedIndicTrans2Repository : IndicTrans2Repository {
    override val provenance = IndicTrans2Provenance.RECORDED_DESKTOP_RUN

    private class Recorded(
        val hindi: String,
        val output: String,
        val targetTokenIds: List<Int>,
        val sameWithoutFinalPunctuation: Boolean,
    )

    private val recorded = listOf(
        Recorded("किताब", "ᱯᱚᱛᱚᱵ ᱾", listOf(103129, 31428, 2), sameWithoutFinalPunctuation = false),
        Recorded("एक", "ᱢᱤᱫᱴᱟᱝ ᱾", listOf(64583, 31428, 2), sameWithoutFinalPunctuation = false),
        Recorded(
            "बहुत अच्छा।", "ᱟᱹᱰᱤ ᱱᱟᱯᱟᱭ ᱾", listOf(78645, 93706, 31428, 2),
            sameWithoutFinalPunctuation = true,
        ),
        Recorded(
            "तुम्हारा नाम क्या है?", "ᱟᱢᱟᱜ ᱧᱩᱛᱩᱢ ᱪᱮᱫ?", listOf(79072, 81465, 88077, 11, 2),
            sameWithoutFinalPunctuation = true,
        ),
        // Translation verified, but no audio passed the quality check: shown as text only.
        Recorded(
            "अपना नाम लिखो।", "ᱟᱢᱟᱜ ᱧᱩᱛᱩᱢ ᱚᱞ ᱢᱮ ᱾", listOf(79072, 81465, 85079, 67823, 31428, 2),
            sameWithoutFinalPunctuation = true,
        ),
    )

    private val exact: Map<String, Recorded> =
        recorded.associateBy { PhrasePackTranslationRepository.normalize(it.hindi) }
    private val withoutFinalPunctuation: Map<String, Recorded> = recorded
        .filter { it.sameWithoutFinalPunctuation }
        .associateBy { stripFinalPunctuation(PhrasePackTranslationRepository.normalize(it.hindi)) }

    override val knownPhrases: List<String> = recorded.map { it.hindi }

    override fun translate(hindi: String): IndicTrans2Result? {
        val key = PhrasePackTranslationRepository.normalize(hindi)
        if (key.isEmpty()) return null
        val entry = exact[key] ?: withoutFinalPunctuation[stripFinalPunctuation(key)] ?: return null
        // The result names the recorded Hindi, so audio is matched against the phrase that was translated.
        return IndicTrans2Result(entry.hindi, entry.output, entry.targetTokenIds, provenance)
    }

    private companion object {
        fun stripFinalPunctuation(text: String): String = text.trimEnd { it.isWhitespace() || it in "।॥.?!" }
    }
}
