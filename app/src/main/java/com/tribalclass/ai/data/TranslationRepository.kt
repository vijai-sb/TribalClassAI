package com.tribalclass.ai.data

import java.text.Normalizer

/**
 * Hindi → Santali translation source used by the UI. The current implementation looks phrases up
 * in the offline pack; a model-backed implementation can replace it without UI changes.
 */
interface TranslationRepository {
    /** Returns the stored translation for [hindi], or null if none exists. Never invents text. */
    fun translate(hindi: String): TranslationEntry?
}

/**
 * Exact-match lookup against a fixed list of entries. Input and keys are normalised the same
 * way (Unicode NFC, trimmed, internal whitespace collapsed); there is no fuzzy matching.
 */
class PhrasePackTranslationRepository(
    entries: List<TranslationEntry> = OfflinePhrasePack.entries,
) : TranslationRepository {

    private val byHindi: Map<String, TranslationEntry> = entries.associateBy { normalize(it.hindi) }

    override fun translate(hindi: String): TranslationEntry? {
        val key = normalize(hindi)
        if (key.isEmpty()) return null
        return byHindi[key]
    }

    companion object {
        // Android's ICU regex treats \s as Unicode whitespace (incl. no-break space); it rejects (?U).
        private val WHITESPACE = Regex("""\s+""")

        fun normalize(text: String): String =
            Normalizer.normalize(text, Normalizer.Form.NFC).trim().replace(WHITESPACE, " ")
    }
}
