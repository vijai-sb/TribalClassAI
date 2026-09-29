package com.tribalclass.ai.speech

import android.content.Context

/**
 * Hindi speech-to-text engine. Implementations must run fully on the device and must never fall
 * back to an online service. All methods are called, and all results delivered, on the main thread.
 */
interface HindiSpeechRecognizer {
    /** False when no engine or model is installed; the UI then shows speech input as unavailable. */
    val isAvailable: Boolean

    /**
     * Opens the microphone and starts recognising. [onResult] receives [AsrResult] events and is
     * called at least once more after this returns; the attempt ends with [AsrResult.Final] or
     * [AsrResult.Error]. The caller must already hold the RECORD_AUDIO permission.
     */
    fun start(onResult: (AsrResult) -> Unit)

    /** Stops capturing and recognises what was heard so far. */
    fun stop()

    /** Abandons the current attempt without a result and closes the microphone. */
    fun cancel()

    /** Frees the engine, model and microphone. The recognizer can't be used afterwards. */
    fun release()
}

/**
 * Stand-in used when the on-device Hindi model is not installed. It reports itself unavailable and never
 * opens the microphone or produces text.
 */
class UnavailableHindiSpeechRecognizer : HindiSpeechRecognizer {
    override val isAvailable: Boolean = false

    override fun start(onResult: (AsrResult) -> Unit) {
        onResult(AsrResult.Error(AsrError.ENGINE_UNAVAILABLE))
    }

    override fun stop() = Unit

    override fun cancel() = Unit

    override fun release() = Unit
}

/** The single place that chooses the Hindi speech engine for the app. */
object HindiSpeechRecognizers {
    /** The on-device sherpa-onnx recognizer if the model files are installed, otherwise unavailable. */
    fun create(context: Context): HindiSpeechRecognizer =
        HindiAsrModel.find(context)?.let { SherpaOnnxHindiSpeechRecognizer(it) }
            ?: UnavailableHindiSpeechRecognizer()
}
