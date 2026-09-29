package com.tribalclass.ai.speech

import android.content.Context
import java.io.File

/**
 * Location of the on-device Hindi ASR model. The ~198 MB model is not packaged in the APK; the
 * native runtime reads it straight from app-specific storage, so it is never copied through Java
 * memory or duplicated from APK assets.
 *
 * Expected files, from Hugging Face `parismitaglobalsolutions/indicconformer-sherpa-onnx`
 * (commit 9721eb71): `hi/model.int8.onnx` and the shared `tokens.txt`. Upstream checkpoint:
 * `ai4bharat/indicconformer_stt_hi_hybrid_ctc_rnnt_large` (MIT).
 *
 * Searched in order:
 *  1. <filesDir>/models/asr/hi/  (/data/user/0/com.tribalclass.ai/files/models/asr/hi/)
 *  2. <externalFilesDir>/models/asr/hi/  (/sdcard/Android/data/com.tribalclass.ai/files/models/asr/hi/)
 *
 * For development, install into (1) on a debug build: `adb push` the files to /data/local/tmp,
 * then `adb shell run-as com.tribalclass.ai` to copy them into files/models/asr/hi/. Files pushed
 * by adb straight into (2) were not visible to the app on the API 36 emulator.
 */
class HindiAsrModel private constructor(val model: File, val tokens: File) {

    companion object {
        const val MODEL_FILE = "model.int8.onnx"
        const val TOKENS_FILE = "tokens.txt"
        private const val RELATIVE_DIR = "models/asr/hi"

        /** Returns the model if both files are present in one of the searched directories. */
        fun find(context: Context): HindiAsrModel? =
            listOfNotNull(context.filesDir, context.getExternalFilesDir(null))
                .map { File(it, RELATIVE_DIR) }
                .map { HindiAsrModel(File(it, MODEL_FILE), File(it, TOKENS_FILE)) }
                .firstOrNull { it.model.isFile && it.model.length() > 0 && it.tokens.isFile }
    }
}
