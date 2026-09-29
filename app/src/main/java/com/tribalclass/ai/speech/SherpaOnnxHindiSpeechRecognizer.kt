package com.tribalclass.ai.speech

import android.annotation.SuppressLint
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Handler
import android.os.Looper
import android.util.Log
import com.k2fsa.sherpa.onnx.FeatureConfig
import com.k2fsa.sherpa.onnx.OfflineModelConfig
import com.k2fsa.sherpa.onnx.OfflineNemoEncDecCtcModelConfig
import com.k2fsa.sherpa.onnx.OfflineRecognizer
import com.k2fsa.sherpa.onnx.OfflineRecognizerConfig
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.Future

/**
 * On-device Hindi recognition with sherpa-onnx and AI4Bharat IndicConformer (CTC, int8).
 *
 * The model is non-streaming, so audio is recorded until [stop] (or [MAX_SECONDS]) and then
 * decoded in one pass; no partial text is produced. The model starts loading in the background as
 * soon as this is created. Nothing here uses the network.
 */
class SherpaOnnxHindiSpeechRecognizer(model: HindiAsrModel) : HindiSpeechRecognizer {

    private val main = Handler(Looper.getMainLooper())

    // All native recognizer calls (load, decode, release) run on this one thread.
    private val engineExecutor: ExecutorService = Executors.newSingleThreadExecutor()
    private val engine: Future<OfflineRecognizer?> = engineExecutor.submit<OfflineRecognizer?> {
        try {
            val startNs = System.nanoTime()
            OfflineRecognizer(config = recognizerConfig(model)).also {
                val ms = (System.nanoTime() - startNs) / 1_000_000
                Log.i(TAG, "sherpa-onnx recognizer loaded in $ms ms from ${model.model.parent}")
            }
        } catch (e: Throwable) { // native load failure, bad model file, missing ABI
            Log.e(TAG, "Failed to initialise sherpa-onnx recognizer", e)
            null
        }
    }

    private var session: Session? = null
    private var released = false

    override val isAvailable: Boolean
        get() = !released && !(engine.isDone && engine.get() == null)

    @SuppressLint("MissingPermission") // The interface requires callers to hold RECORD_AUDIO.
    override fun start(onResult: (AsrResult) -> Unit) {
        cancel()
        if (!isAvailable) {
            onResult(AsrResult.Error(AsrError.ENGINE_UNAVAILABLE))
            return
        }
        val record = try {
            val minBuffer = AudioRecord.getMinBufferSize(SAMPLE_RATE, CHANNEL, ENCODING)
            if (minBuffer <= 0) {
                null
            } else {
                AudioRecord(
                    MediaRecorder.AudioSource.VOICE_RECOGNITION,
                    SAMPLE_RATE,
                    CHANNEL,
                    ENCODING,
                    maxOf(minBuffer, SAMPLE_RATE / 5 * 2),
                ).takeIf { it.state == AudioRecord.STATE_INITIALIZED }
            }
        } catch (e: RuntimeException) { // SecurityException, IllegalArgumentException
            Log.w(TAG, "Could not open microphone", e)
            null
        }
        if (record == null) {
            onResult(AsrResult.Error(AsrError.MICROPHONE_UNAVAILABLE))
            return
        }
        try {
            record.startRecording()
        } catch (e: IllegalStateException) {
            Log.w(TAG, "Could not start recording", e)
        }
        if (record.recordingState != AudioRecord.RECORDSTATE_RECORDING) {
            record.release()
            onResult(AsrResult.Error(AsrError.MICROPHONE_UNAVAILABLE))
            return
        }
        val newSession = Session(record, onResult)
        session = newSession
        onResult(AsrResult.Listening)
        newSession.capture.start()
    }

    override fun stop() {
        // The capture thread sees this, closes the microphone and decodes what it has.
        session?.recording = false
    }

    override fun cancel() {
        val current = session ?: return
        session = null
        current.cancelled = true
        current.recording = false
    }

    override fun release() {
        if (released) return
        released = true
        cancel()
        engineExecutor.execute { runCatching { engine.get() }.getOrNull()?.release() }
        engineExecutor.shutdown()
    }

    /** One recording attempt. The capture thread owns the AudioRecord. */
    private inner class Session(
        private val record: AudioRecord,
        private val onResult: (AsrResult) -> Unit,
    ) {
        @Volatile var recording = true
        @Volatile var cancelled = false

        val capture = Thread({ captureAndDecode() }, "hindi-asr-capture")

        private fun captureAndDecode() {
            val maxSamples = SAMPLE_RATE * MAX_SECONDS
            val audio = FloatArray(maxSamples)
            val chunk = ShortArray(SAMPLE_RATE / 10)
            var count = 0
            var micFailed = false
            try {
                while (recording && count < maxSamples) {
                    val n = record.read(chunk, 0, minOf(chunk.size, maxSamples - count))
                    if (n < 0) {
                        micFailed = true
                        break
                    }
                    for (i in 0 until n) audio[count + i] = chunk[i] / 32768f
                    count += n
                }
            } finally {
                runCatching { record.stop() }
                record.release()
            }
            if (cancelled) return
            var peak = 0f
            for (i in 0 until count) peak = maxOf(peak, kotlin.math.abs(audio[i]))
            Log.i(TAG, "Captured %.2f s of audio, peak level %.3f".format(count.toFloat() / SAMPLE_RATE, peak))
            when {
                micFailed -> post(AsrResult.Error(AsrError.MICROPHONE_UNAVAILABLE))
                count < SAMPLE_RATE / 4 -> post(AsrResult.Error(AsrError.NOT_RECOGNIZED))
                else -> {
                    post(AsrResult.Processing)
                    post(decode(audio.copyOf(count)))
                }
            }
        }

        private fun decode(samples: FloatArray): AsrResult = try {
            engineExecutor.submit<AsrResult> {
                val recognizer = engine.get() ?: return@submit AsrResult.Error(AsrError.ENGINE_UNAVAILABLE)
                val stream = recognizer.createStream()
                try {
                    val startNs = System.nanoTime()
                    stream.acceptWaveform(samples, SAMPLE_RATE)
                    recognizer.decode(stream)
                    val text = recognizer.getResult(stream).text
                    val ms = (System.nanoTime() - startNs) / 1_000_000
                    Log.i(TAG, "Decoded in $ms ms: \"$text\"")
                    AsrResult.Final(text)
                } finally {
                    stream.release()
                }
            }.get()
        } catch (e: Exception) { // decode failure, or executor shut down by release()
            Log.e(TAG, "Decoding failed", e)
            AsrResult.Error(AsrError.NOT_RECOGNIZED)
        }

        private fun post(result: AsrResult) {
            main.post {
                if (!cancelled && session === this) {
                    if (result is AsrResult.Final || result is AsrResult.Error) session = null
                    onResult(result)
                }
            }
        }
    }

    private companion object {
        const val TAG = "HindiAsr"
        const val SAMPLE_RATE = 16_000
        const val CHANNEL = AudioFormat.CHANNEL_IN_MONO
        const val ENCODING = AudioFormat.ENCODING_PCM_16BIT
        const val MAX_SECONDS = 30

        fun recognizerConfig(model: HindiAsrModel) = OfflineRecognizerConfig(
            featConfig = FeatureConfig(sampleRate = SAMPLE_RATE, featureDim = 80),
            modelConfig = OfflineModelConfig(
                nemo = OfflineNemoEncDecCtcModelConfig(model = model.model.absolutePath),
                tokens = model.tokens.absolutePath,
                numThreads = 2,
                provider = "cpu",
            ),
            decodingMethod = "greedy_search",
        )
    }
}
