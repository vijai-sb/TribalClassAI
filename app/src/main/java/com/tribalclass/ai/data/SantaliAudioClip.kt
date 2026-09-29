package com.tribalclass.ai.data

import androidx.annotation.RawRes

/** How a clip's audio was produced, so the UI never presents one kind as another. */
enum class AudioSourceKind {
    /** A recording of a person speaking, bundled in res/raw. Not text-to-speech. */
    PRE_RECORDED,

    /**
     * Speech generated ahead of time by a Santali TTS model and bundled in res/raw for offline
     * playback. Nothing is synthesized on the device.
     */
    PRE_GENERATED_TTS,
}

/** One bundled Santali audio clip for a phrase-pack translation. */
data class SantaliAudioClip(
    /** Hindi source phrase, matched the same way as [TranslationEntry.hindi]. */
    val hindi: String,
    /** The exact Ol Chiki text spoken in the clip; must equal the translation it is played for. */
    val santaliOlChiki: String,
    @param:RawRes val rawResId: Int,
    val kind: AudioSourceKind,
    /** Who recorded it and under what licence or permission, for maintainers. */
    val credit: String,
)
