package com.tribalclass.ai.speech

/** Why a recognition attempt ended without text. */
enum class AsrError {
    /** Audio was captured but no Hindi speech was recognised. */
    NOT_RECOGNIZED,

    /** The microphone could not be opened or stopped delivering audio. */
    MICROPHONE_UNAVAILABLE,

    /** No speech recognition engine or model is installed in this build. */
    ENGINE_UNAVAILABLE,
}

/** Events a [HindiSpeechRecognizer] reports during one recognition attempt. */
sealed interface AsrResult {
    /** The microphone is open and audio is being captured. */
    data object Listening : AsrResult

    /** Capture has ended and the engine is producing the final text. */
    data object Processing : AsrResult

    /** Interim text while listening, if the engine supports it. */
    data class Partial(val text: String) : AsrResult

    /** The recognised Hindi text. Ends the attempt. */
    data class Final(val text: String) : AsrResult

    /** The attempt failed. Ends the attempt. */
    data class Error(val error: AsrError) : AsrResult
}
