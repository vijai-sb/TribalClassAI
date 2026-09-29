package com.tribalclass.ai.data

/**
 * Supplies Santali audio for a translation. The current implementation serves bundled
 * recordings; a future speech-synthesis provider can implement this with its own [AudioSourceKind].
 */
interface SantaliAudioRepository {
    /** Returns the clip for [entry], or null if there is none. Never substitutes other audio. */
    fun audioFor(entry: TranslationEntry): SantaliAudioClip?
}

/**
 * Looks up bundled recordings by Hindi phrase. A clip is only returned when the Ol Chiki text it
 * records matches the translation being shown, so a stale recording can't play for changed text.
 */
class LocalRecordingAudioRepository(
    clips: List<SantaliAudioClip> = SantaliRecordings.clips,
) : SantaliAudioRepository {

    private val byHindi: Map<String, SantaliAudioClip> =
        clips.associateBy { PhrasePackTranslationRepository.normalize(it.hindi) }

    override fun audioFor(entry: TranslationEntry): SantaliAudioClip? {
        val clip = byHindi[PhrasePackTranslationRepository.normalize(entry.hindi)] ?: return null
        val sameText = PhrasePackTranslationRepository.normalize(clip.santaliOlChiki) ==
            PhrasePackTranslationRepository.normalize(entry.santaliOlChiki)
        return clip.takeIf { sameText }
    }
}
