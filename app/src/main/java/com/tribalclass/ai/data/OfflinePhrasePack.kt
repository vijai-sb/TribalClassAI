package com.tribalclass.ai.data

/**
 * The offline Hindi → Santali (Ol Chiki) phrase pack.
 *
 * Only translations that already exist from the project's feasibility work are listed here.
 * Lesson items without an entry are intentionally missing: the app reports them as unavailable
 * rather than guessing. Add new entries only from a traceable source, and use HUMAN_VERIFIED
 * only after a Santali speaker has checked the text.
 */
object OfflinePhrasePack {
    private const val INDICTRANS2_FEASIBILITY =
        "IndicTrans2 indic-indic 320M (ONNX) feasibility run; identical output across fp32/int8 and greedy/beam-4 decoding"

    // Entries below were added from the same feasibility logs under the same bar: identical output in
    // (nearly) all 10 runs, back-translation to the source Hindi, and agreement with the community
    // Santali word used as a check in that test. See tools/santali_tts_test/prototype_audio/
    // feasibility_mt_consistency.txt.
    private const val INDICTRANS2_FEASIBILITY_10_OF_10 =
        "IndicTrans2 indic-indic 320M (ONNX) feasibility run; identical output in 10/10 runs; back-translates to the source"
    private const val INDICTRANS2_FEASIBILITY_9_OF_10 =
        "IndicTrans2 indic-indic 320M (ONNX) feasibility run; identical output in 9/10 runs; back-translates to the source meaning"

    val entries: List<TranslationEntry> = listOf(
        TranslationEntry(
            hindi = "किताब",
            santaliOlChiki = "ᱯᱚᱛᱚᱵ",
            status = TranslationStatus.MODEL_GENERATED_UNREVIEWED,
            source = INDICTRANS2_FEASIBILITY,
        ),
        TranslationEntry(
            hindi = "एक",
            santaliOlChiki = "ᱢᱤᱫᱴᱟᱝ",
            status = TranslationStatus.MODEL_GENERATED_UNREVIEWED,
            source = INDICTRANS2_FEASIBILITY,
        ),
        TranslationEntry(
            hindi = "पानी",
            santaliOlChiki = "ᱫᱟᱜ",
            status = TranslationStatus.MODEL_GENERATED_UNREVIEWED,
            source = INDICTRANS2_FEASIBILITY_10_OF_10,
        ),
        TranslationEntry(
            hindi = "घर",
            santaliOlChiki = "ᱚᱲᱟᱜ",
            status = TranslationStatus.MODEL_GENERATED_UNREVIEWED,
            source = INDICTRANS2_FEASIBILITY_10_OF_10,
        ),
        TranslationEntry(
            hindi = "अपना नाम लिखो।",
            santaliOlChiki = "ᱟᱢᱟᱜ ᱧᱩᱛᱩᱢ ᱚᱞ ᱢᱮ",
            status = TranslationStatus.MODEL_GENERATED_UNREVIEWED,
            source = INDICTRANS2_FEASIBILITY_9_OF_10,
        ),
    )
}
