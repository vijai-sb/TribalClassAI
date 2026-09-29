package com.tribalclass.ai.data

/** One lesson item on a worksheet, with its stored translation if the offline pack has one. */
data class WorksheetItem(
    val hindi: String,
    val translation: TranslationEntry?,
)

/**
 * A bilingual worksheet for one lesson. Built only from the lesson's own Hindi items and the
 * translations that already exist; missing translations stay null and are never filled in.
 */
data class Worksheet(
    val lesson: Lesson,
    val items: List<WorksheetItem>,
) {
    /** Items that have a stored translation; the only ones used in practice activities. */
    val translatedItems: List<TranslationEntry> = items.mapNotNull { it.translation }

    /**
     * Santali side of the matching activity: the translated items rotated by one, so no Santali
     * word sits opposite its own Hindi word. Deterministic, so every run shows the same order.
     */
    val matchingSantaliOrder: List<TranslationEntry> =
        if (translatedItems.size < 2) translatedItems else translatedItems.drop(1) + translatedItems.first()

    companion object {
        /** Minimum number of translated pairs for a matching activity to make sense. */
        const val MIN_MATCHING_PAIRS = 2

        fun build(lesson: Lesson, translator: TranslationRepository): Worksheet = Worksheet(
            lesson = lesson,
            items = lesson.hindiItems.map { WorksheetItem(it, translator.translate(it)) },
        )
    }
}
