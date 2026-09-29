package com.tribalclass.ai.data

/** Where a stored translation came from and whether a person has checked it. */
enum class TranslationStatus {
    /** Produced by a machine translation model; no Santali speaker has reviewed it. */
    MODEL_GENERATED_UNREVIEWED,

    /** Checked and approved by a Santali speaker. */
    HUMAN_VERIFIED,
}

/** One Hindi → Santali pair in the offline phrase pack. */
data class TranslationEntry(
    val hindi: String,
    val santaliOlChiki: String,
    val status: TranslationStatus,
    /** Free-text note on where the translation came from, for maintainers. */
    val source: String,
)
