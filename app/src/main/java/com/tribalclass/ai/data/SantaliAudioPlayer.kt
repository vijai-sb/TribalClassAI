package com.tribalclass.ai.data

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioDeviceInfo
import android.media.AudioFocusRequest
import android.media.AudioManager
import android.media.MediaPlayer
import android.util.Log

/**
 * Plays bundled clips with the platform [MediaPlayer]. One clip plays at a time; call [release]
 * when the owner goes away. All calls must be made on the main thread.
 *
 * Playback uses media/speech audio attributes and transient audio focus, and every step is logged
 * under the "SantaliAudio" tag so device-specific problems (muted media volume, output routing)
 * can be diagnosed from logcat.
 */
class SantaliAudioPlayer(context: Context) {
    private val appContext = context.applicationContext
    private val audioManager = appContext.getSystemService(Context.AUDIO_SERVICE) as AudioManager
    private val attributes = AudioAttributes.Builder()
        .setUsage(AudioAttributes.USAGE_MEDIA)
        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
        .build()
    private val focusRequest = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)
        .setAudioAttributes(attributes)
        .build()
    private var player: MediaPlayer? = null

    /** True when the media volume (the stream these clips play on) is at zero. */
    fun isMediaVolumeMuted(): Boolean = audioManager.getStreamVolume(AudioManager.STREAM_MUSIC) == 0

    /**
     * Starts [clip], stopping anything already playing. Returns false, without throwing, if the
     * resource is missing or can't be decoded. [onFinished] runs when playback ends or fails.
     */
    fun play(clip: SantaliAudioClip, onFinished: () -> Unit): Boolean {
        stop()
        val name = runCatching { appContext.resources.getResourceEntryName(clip.rawResId) }.getOrDefault("?")
        Log.i(
            TAG,
            "play ${clip.santaliOlChiki}: res/raw/$name (0x${Integer.toHexString(clip.rawResId)}), " +
                "media volume ${audioManager.getStreamVolume(AudioManager.STREAM_MUSIC)}/" +
                "${audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC)}, outputs ${outputDevices()}",
        )

        val mp = MediaPlayer()
        try {
            mp.setAudioAttributes(attributes)
            // Raw WAVs are stored uncompressed in the APK, so they can be read through a file descriptor.
            appContext.resources.openRawResourceFd(clip.rawResId).use { afd ->
                mp.setDataSource(afd.fileDescriptor, afd.startOffset, afd.length)
            }
            mp.prepare() // a short local file; preparing synchronously is quick
        } catch (e: Exception) { // Resources.NotFoundException, IOException, IllegalStateException
            Log.e(TAG, "could not prepare res/raw/$name", e)
            mp.release()
            return false
        }
        Log.i(TAG, "MediaPlayer created and prepared: ${mp.duration} ms")

        mp.setOnCompletionListener {
            Log.i(TAG, "completed res/raw/$name")
            stop()
            onFinished()
        }
        mp.setOnErrorListener { _, what, extra ->
            Log.e(TAG, "playback error res/raw/$name: what=$what extra=$extra")
            stop()
            onFinished()
            true
        }
        player = mp
        val focus = audioManager.requestAudioFocus(focusRequest)
        Log.i(TAG, "audio focus ${if (focus == AudioManager.AUDIOFOCUS_REQUEST_GRANTED) "granted" else "not granted ($focus)"}")
        mp.start()
        Log.i(TAG, "started res/raw/$name, isPlaying=${mp.isPlaying}")
        return true
    }

    fun stop() {
        val mp = player ?: return
        player = null
        try {
            if (mp.isPlaying) {
                mp.stop()
                Log.i(TAG, "stopped")
            }
        } catch (e: IllegalStateException) {
            // Already stopped or in an error state; releasing is still safe.
        }
        mp.release()
        audioManager.abandonAudioFocusRequest(focusRequest)
        Log.i(TAG, "released")
    }

    fun release() = stop()

    private fun outputDevices(): String =
        audioManager.getDevices(AudioManager.GET_DEVICES_OUTPUTS).joinToString(prefix = "[", postfix = "]") {
            when (it.type) {
                AudioDeviceInfo.TYPE_BUILTIN_SPEAKER -> "speaker"
                AudioDeviceInfo.TYPE_BUILTIN_EARPIECE -> "earpiece"
                AudioDeviceInfo.TYPE_WIRED_HEADPHONES, AudioDeviceInfo.TYPE_WIRED_HEADSET -> "wired"
                AudioDeviceInfo.TYPE_BLUETOOTH_A2DP, AudioDeviceInfo.TYPE_BLUETOOTH_SCO -> "bluetooth"
                AudioDeviceInfo.TYPE_USB_DEVICE, AudioDeviceInfo.TYPE_USB_HEADSET -> "usb"
                else -> "type${it.type}"
            }
        }

    private companion object {
        const val TAG = "SantaliAudio"
    }
}
