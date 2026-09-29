package com.tribalclass.ai.speech

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

/**
 * Turns [HindiSpeechRecognizer] events into an [AsrState] for the UI, so screens only deal with
 * button presses and the final text. Permission requests stay with the screen.
 */
class HindiSpeechInput(private val recognizer: HindiSpeechRecognizer) {

    var state: AsrState by mutableStateOf(if (recognizer.isAvailable) AsrState.Idle else AsrState.Unavailable)
        private set

    val isAvailable: Boolean get() = recognizer.isAvailable

    /** Starts listening. [onText] receives the recognised Hindi text once, if any is recognised. */
    fun start(onText: (String) -> Unit) {
        if (!recognizer.isAvailable) {
            state = AsrState.Unavailable
            return
        }
        state = AsrState.Listening()
        recognizer.start { result ->
            when (result) {
                AsrResult.Listening -> state = AsrState.Listening()
                AsrResult.Processing -> state = AsrState.Recognizing
                is AsrResult.Partial -> state = AsrState.Listening(result.text)
                is AsrResult.Final -> {
                    val text = result.text.trim()
                    if (text.isEmpty()) {
                        state = AsrState.Failed(AsrError.NOT_RECOGNIZED)
                    } else {
                        state = AsrState.Idle
                        onText(text)
                    }
                }
                is AsrResult.Error -> state = if (result.error == AsrError.ENGINE_UNAVAILABLE) {
                    AsrState.Unavailable
                } else {
                    AsrState.Failed(result.error)
                }
            }
        }
    }

    /** Stops listening and recognises what was said so far. */
    fun stop() {
        if (state is AsrState.Listening) {
            state = AsrState.Recognizing
            recognizer.stop()
        }
    }

    fun onPermissionDenied() {
        state = AsrState.PermissionDenied
    }

    /** Cancels any attempt and frees the recognizer; call when the screen goes away. */
    fun release() {
        recognizer.cancel()
        recognizer.release()
    }
}
