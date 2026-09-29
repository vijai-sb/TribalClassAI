package com.tribalclass.ai.speech

/** What the Hindi speech input control should show. */
sealed interface AsrState {
    /** Ready to start listening. */
    data object Idle : AsrState

    /** Capturing audio; [partialText] is interim text if the engine provides it. */
    data class Listening(val partialText: String = "") : AsrState

    /** Capture has ended; waiting for the final text. */
    data object Recognizing : AsrState

    /** The last attempt failed. */
    data class Failed(val error: AsrError) : AsrState

    /** The user refused microphone permission. */
    data object PermissionDenied : AsrState

    /** This build has no speech recognition engine, so the control cannot be used. */
    data object Unavailable : AsrState
}
