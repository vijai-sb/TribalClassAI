package com.tribalclass.ai.ui.teacher

import android.Manifest
import android.content.pm.PackageManager
import android.util.Log
import androidx.annotation.StringRes
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.consumeWindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.tribalclass.ai.R
import com.tribalclass.ai.data.DemoLessons
import com.tribalclass.ai.data.IndicTrans2Repository
import com.tribalclass.ai.data.RecordedIndicTrans2Repository
import com.tribalclass.ai.data.AudioSourceKind
import com.tribalclass.ai.data.Lesson
import com.tribalclass.ai.data.LocalRecordingAudioRepository
import com.tribalclass.ai.data.SantaliAudioClip
import com.tribalclass.ai.data.SantaliAudioPlayer
import com.tribalclass.ai.data.SantaliAudioRepository
import com.tribalclass.ai.data.PhrasePackTranslationRepository
import com.tribalclass.ai.data.TranslationEntry
import com.tribalclass.ai.data.TranslationRepository
import com.tribalclass.ai.speech.AsrError
import com.tribalclass.ai.speech.AsrState
import com.tribalclass.ai.speech.HindiSpeechInput
import com.tribalclass.ai.speech.HindiSpeechRecognizer
import com.tribalclass.ai.speech.HindiSpeechRecognizers
import com.tribalclass.ai.ui.components.LessonTopicSelector
import com.tribalclass.ai.ui.components.StatusBadge
import com.tribalclass.ai.ui.components.TranslationStatusLabel
import com.tribalclass.ai.ui.theme.ReadyGreen
import com.tribalclass.ai.ui.theme.TribalClassTheme

/**
 * Teacher Mode layout. Translation looks phrases up in the offline pack via [translator];
 * audio plays bundled Santali recordings from [audioRepository] when one exists for the result.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TeacherModeScreen(
    onBack: () -> Unit,
    translator: TranslationRepository = remember { PhrasePackTranslationRepository() },
    audioRepository: SantaliAudioRepository = remember { LocalRecordingAudioRepository() },
    speechRecognizer: HindiSpeechRecognizer? = null,
    indicTrans2: IndicTrans2Repository = remember { RecordedIndicTrans2Repository() },
) {
    // Only ids and text are saved; lessons and translations are looked up again after rotation.
    var selectedLessonId by rememberSaveable { mutableStateOf(DemoLessons.default.id) }
    val selectedLesson = DemoLessons.byId(selectedLessonId)
    var hindiText by rememberSaveable { mutableStateOf("") }
    // The Hindi text the last Translate press was for; null until pressed or after the input changes.
    var translatedHindi by rememberSaveable { mutableStateOf<String?>(null) }
    val result = translatedHindi?.let { translator.translate(it) }
    // Audio is only ever looked up for a translation that exists.
    val clip = result?.let { audioRepository.audioFor(it) }

    val context = LocalContext.current
    val audioPlayer = remember { SantaliAudioPlayer(context) }
    var playingClip by remember { mutableStateOf<SantaliAudioClip?>(null) }
    var playbackFailed by remember { mutableStateOf(false) }
    var volumeMuted by remember { mutableStateOf(false) }
    // Releases the player when Teacher Mode leaves the screen.
    DisposableEffect(audioPlayer) {
        onDispose { audioPlayer.release() }
    }
    // Stops playback whenever the clip for the shown translation changes.
    DisposableEffect(clip) {
        onDispose {
            audioPlayer.stop()
            playingClip = null
            playbackFailed = false
            volumeMuted = false
        }
    }

    fun updateInput(text: String) {
        hindiText = text
        translatedHindi = null
    }

    val speechInput = remember(speechRecognizer) {
        HindiSpeechInput(speechRecognizer ?: HindiSpeechRecognizers.create(context))
    }
    // Cancels listening and frees the recognizer and microphone when Teacher Mode goes away.
    DisposableEffect(speechInput) {
        onDispose { speechInput.release() }
    }
    // "Hindi → Santali Audio": ASR text → IndicTrans2 → Ol Chiki → matching cached clip, played at once.
    var s2aRun by remember { mutableStateOf<HindiToSantaliRun?>(null) }

    fun runHindiToSantaliAudio(hindi: String, source: HindiSource) {
        val translation = indicTrans2.translate(hindi)
        // The existing audio repository only returns a clip whose Hindi and Ol Chiki both match.
        val s2aClip = translation?.let { audioRepository.audioFor(it.toTranslationEntry()) }
        Log.i(
            "HindiSantaliAudio",
            "hindi=\"$hindi\" (source=$source) lookup=\"${translation?.hindi}\" indicTrans2=\"${translation?.rawOutput}\" " +
                "(${translation?.provenance}, ids=${translation?.targetTokenIds}) " +
                "matchText=\"${translation?.olChikiForAudio}\" clip=${s2aClip?.let { context.resources.getResourceEntryName(it.rawResId) }}",
        )
        s2aRun = HindiToSantaliRun(hindi, source, translation, s2aClip)
        if (s2aClip != null) {
            val started = audioPlayer.play(s2aClip, onFinished = { playingClip = null })
            playingClip = if (started) s2aClip else null
        } else {
            audioPlayer.stop()
            playingClip = null
        }
    }

    // Which control the shared recognizer is serving: the Hindi box, or the Hindi → Santali Audio section.
    var asrForS2a by remember { mutableStateOf(false) }

    fun startListening() {
        if (asrForS2a) speechInput.start { runHindiToSantaliAudio(it, HindiSource.SPEECH) } else speechInput.start(::updateInput)
    }

    val micPermissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        if (granted) startListening() else speechInput.onPermissionDenied()
    }

    fun onMicClick(forS2a: Boolean) {
        when {
            speechInput.state is AsrState.Listening || speechInput.state == AsrState.Recognizing -> {
                if (asrForS2a == forS2a) speechInput.stop()
            }
            else -> {
                asrForS2a = forS2a
                if (ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) ==
                    PackageManager.PERMISSION_GRANTED
                ) {
                    startListening()
                } else {
                    micPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                }
            }
        }
    }
    val inactiveAsrState = if (speechInput.isAvailable) AsrState.Idle else AsrState.Unavailable

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text(stringResource(R.string.feature_teacher_title)) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            painter = painterResource(R.drawable.ic_arrow_back),
                            contentDescription = stringResource(R.string.navigate_back),
                        )
                    }
                },
            )
        },
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .consumeWindowInsets(padding)
                .imePadding(),
            contentAlignment = Alignment.TopCenter,
        ) {
            Column(
                modifier = Modifier
                    .widthIn(max = 640.dp)
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 20.dp, vertical = 16.dp),
                verticalArrangement = Arrangement.spacedBy(20.dp),
            ) {
                LanguageHeader()
                LessonTopicSelector(
                    lessons = DemoLessons.all,
                    selected = selectedLesson,
                    onSelect = { selectedLessonId = it.id },
                )
                LessonContent(lesson = selectedLesson, onItemClick = ::updateInput)
                HindiInput(value = hindiText, onValueChange = ::updateInput)
                SpeechInputControl(
                    state = if (asrForS2a) inactiveAsrState else speechInput.state,
                    onClick = { onMicClick(forS2a = false) },
                )
                TranslateAction(
                    enabled = hindiText.isNotBlank(),
                    onTranslate = { translatedHindi = hindiText },
                )
                ResultArea(attempted = translatedHindi != null, result = result)
                AudioSection(
                    clip = clip,
                    hasTranslation = result != null,
                    isPlaying = clip != null && playingClip == clip,
                    playbackFailed = playbackFailed,
                    volumeMuted = volumeMuted,
                    onPlay = { toPlay ->
                        val started = audioPlayer.play(toPlay, onFinished = { playingClip = null })
                        playingClip = if (started) toPlay else null
                        playbackFailed = !started
                        volumeMuted = started && audioPlayer.isMediaVolumeMuted()
                    },
                    onStop = {
                        audioPlayer.stop()
                        playingClip = null
                    },
                )
                HindiToSantaliAudioSection(
                    asrState = if (asrForS2a) speechInput.state else inactiveAsrState,
                    run = s2aRun,
                    isPlaying = s2aRun?.clip != null && playingClip == s2aRun?.clip,
                    canUseTypedText = hindiText.isNotBlank(),
                    phrases = indicTrans2.knownPhrases,
                    onRecordClick = { onMicClick(forS2a = true) },
                    onUseTypedText = { runHindiToSantaliAudio(hindiText, HindiSource.TYPED) },
                    onPhraseClick = { runHindiToSantaliAudio(it, HindiSource.PHRASE_BUTTON) },
                    onPlayAgain = { toPlay ->
                        val started = audioPlayer.play(toPlay, onFinished = { playingClip = null })
                        playingClip = if (started) toPlay else null
                    },
                )
            }
        }
    }
}

@Composable
private fun LanguageHeader() {
    val colors = MaterialTheme.colorScheme
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        color = colors.primary,
        contentColor = colors.onPrimary,
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.teacher_language_pair),
                style = MaterialTheme.typography.headlineSmall,
            )
            Surface(
                modifier = Modifier.padding(top = 8.dp),
                shape = RoundedCornerShape(12.dp),
                color = colors.secondaryContainer,
                contentColor = colors.onSecondaryContainer,
            ) {
                Text(
                    text = stringResource(R.string.teacher_script),
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.padding(horizontal = 14.dp, vertical = 6.dp),
                )
            }
            StatusBadge(
                label = stringResource(R.string.teacher_status_offline),
                dotColor = ReadyGreen,
                modifier = Modifier.padding(top = 14.dp),
            )
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun LessonContent(lesson: Lesson, onItemClick: (String) -> Unit) {
    val colors = MaterialTheme.colorScheme
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        color = colors.surfaceVariant,
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Column {
                Text(
                    text = lesson.title,
                    style = MaterialTheme.typography.titleLarge,
                    color = colors.onSurface,
                )
                Text(
                    text = lesson.description,
                    style = MaterialTheme.typography.bodyMedium,
                    color = colors.onSurfaceVariant,
                    modifier = Modifier.padding(top = 2.dp),
                )
            }
            Text(
                text = stringResource(R.string.teacher_lesson_hindi_label),
                style = MaterialTheme.typography.labelLarge,
                color = colors.onSurfaceVariant,
            )
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                lesson.hindiItems.forEach { item ->
                    Surface(
                        onClick = { onItemClick(item) },
                        shape = RoundedCornerShape(12.dp),
                        color = colors.surface,
                        contentColor = colors.onSurface,
                    ) {
                        Text(
                            text = item,
                            style = MaterialTheme.typography.titleLarge,
                            modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp),
                        )
                    }
                }
            }
            Text(
                text = stringResource(R.string.teacher_lesson_tap_hint),
                style = MaterialTheme.typography.bodySmall,
                fontStyle = FontStyle.Italic,
                color = colors.onSurfaceVariant,
            )
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                color = colors.tertiaryContainer,
                contentColor = colors.onTertiaryContainer,
            ) {
                Column(modifier = Modifier.padding(14.dp)) {
                    Text(
                        text = stringResource(R.string.teacher_lesson_activity_label),
                        style = MaterialTheme.typography.labelLarge,
                    )
                    Text(
                        text = lesson.activity,
                        style = MaterialTheme.typography.bodyLarge,
                        modifier = Modifier.padding(top = 4.dp),
                    )
                }
            }
        }
    }
}

@Composable
private fun HindiInput(value: String, onValueChange: (String) -> Unit) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        modifier = Modifier.fillMaxWidth(),
        label = { Text(stringResource(R.string.teacher_input_label)) },
        placeholder = { Text(stringResource(R.string.teacher_input_placeholder)) },
        textStyle = MaterialTheme.typography.titleLarge,
        minLines = 3,
        shape = RoundedCornerShape(16.dp),
    )
}

/** Microphone button for Hindi speech input; recognised text goes into the Hindi field. */
@Composable
internal fun SpeechInputControl(
    state: AsrState,
    onClick: () -> Unit,
    @StringRes idleLabelRes: Int = R.string.speech_speak_hindi,
) {
    val colors = MaterialTheme.colorScheme
    val labelRes = when (state) {
        is AsrState.Listening -> R.string.speech_listening
        AsrState.Recognizing -> R.string.speech_recognizing
        else -> idleLabelRes
    }
    val message = when (state) {
        is AsrState.Failed -> stringResource(
            when (state.error) {
                AsrError.NOT_RECOGNIZED -> R.string.speech_error_not_recognized
                AsrError.MICROPHONE_UNAVAILABLE -> R.string.speech_error_microphone
                AsrError.ENGINE_UNAVAILABLE -> R.string.speech_unavailable
            },
        )
        AsrState.PermissionDenied -> stringResource(R.string.speech_permission_denied)
        AsrState.Unavailable -> stringResource(R.string.speech_unavailable)
        is AsrState.Listening -> state.partialText.ifBlank { stringResource(R.string.speech_tap_to_stop) }
        else -> null
    }
    val listening = state is AsrState.Listening
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        FilledTonalButton(
            onClick = onClick,
            enabled = state != AsrState.Unavailable && state != AsrState.Recognizing,
            modifier = Modifier.heightIn(min = 48.dp),
            colors = if (listening) {
                ButtonDefaults.filledTonalButtonColors(
                    containerColor = colors.secondary,
                    contentColor = colors.onSecondary,
                )
            } else {
                ButtonDefaults.filledTonalButtonColors()
            },
        ) {
            Icon(
                painter = painterResource(if (listening) R.drawable.ic_stop else R.drawable.ic_mic),
                contentDescription = null,
                modifier = Modifier.size(20.dp),
            )
            Text(
                text = stringResource(labelRes),
                style = MaterialTheme.typography.titleSmall,
                modifier = Modifier.padding(start = 8.dp),
            )
        }
        if (message != null) {
            Text(
                text = message,
                style = MaterialTheme.typography.bodyMedium,
                color = if (state is AsrState.Failed) colors.error else colors.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun TranslateAction(enabled: Boolean, onTranslate: () -> Unit) {
    Button(
        onClick = onTranslate,
        enabled = enabled,
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 56.dp),
        shape = RoundedCornerShape(16.dp),
    ) {
        Text(
            text = stringResource(R.string.teacher_translate),
            style = MaterialTheme.typography.titleMedium,
        )
    }
}

@Composable
private fun ResultArea(attempted: Boolean, result: TranslationEntry?) {
    val colors = MaterialTheme.colorScheme
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        SectionLabel(stringResource(R.string.teacher_result_label))
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = 96.dp),
            shape = RoundedCornerShape(16.dp),
            color = colors.surfaceVariant,
        ) {
            if (result != null) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Text(
                        text = result.santaliOlChiki,
                        style = MaterialTheme.typography.headlineMedium,
                        color = colors.onSurface,
                    )
                    TranslationStatusLabel(result.status)
                }
            } else {
                Text(
                    text = stringResource(
                        if (attempted) R.string.teacher_result_not_available
                        else R.string.teacher_result_placeholder,
                    ),
                    style = MaterialTheme.typography.titleMedium,
                    fontStyle = FontStyle.Italic,
                    color = colors.onSurfaceVariant,
                    modifier = Modifier.padding(16.dp),
                )
            }
        }
    }
}

/**
 * Santali audio for the shown translation. Clips are bundled files (pre-generated with a TTS model
 * or recorded); nothing is synthesized on the device. The section says plainly when a cached
 * phrase has no audio.
 */
@Composable
private fun AudioSection(
    clip: SantaliAudioClip?,
    hasTranslation: Boolean,
    isPlaying: Boolean,
    playbackFailed: Boolean,
    volumeMuted: Boolean,
    onPlay: (SantaliAudioClip) -> Unit,
    onStop: () -> Unit,
) {
    val colors = MaterialTheme.colorScheme
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        SectionLabel(stringResource(R.string.teacher_audio_label))
        FilledTonalButton(
            onClick = { if (isPlaying) onStop() else clip?.let(onPlay) },
            enabled = clip != null,
            modifier = Modifier.heightIn(min = 52.dp),
            colors = if (isPlaying) {
                ButtonDefaults.filledTonalButtonColors(
                    containerColor = colors.secondary,
                    contentColor = colors.onSecondary,
                )
            } else {
                ButtonDefaults.filledTonalButtonColors()
            },
        ) {
            Icon(
                painter = painterResource(if (isPlaying) R.drawable.ic_stop else R.drawable.ic_volume),
                contentDescription = null,
                modifier = Modifier.size(22.dp),
            )
            Text(
                text = stringResource(if (isPlaying) R.string.teacher_stop_audio else R.string.teacher_play_audio),
                style = MaterialTheme.typography.titleSmall,
                modifier = Modifier.padding(start = 8.dp),
            )
        }
        if (clip != null) {
            AudioKindLabel(clip.kind)
        }
        val message = when {
            clip == null && hasTranslation -> R.string.teacher_audio_unavailable_for_phrase
            clip == null -> R.string.teacher_audio_not_available
            playbackFailed -> R.string.teacher_audio_playback_failed
            volumeMuted -> R.string.teacher_audio_volume_muted
            else -> null
        }
        if (message != null) {
            Text(
                text = stringResource(message),
                style = MaterialTheme.typography.bodyMedium,
                color = if (volumeMuted || playbackFailed) colors.error else colors.onSurfaceVariant,
            )
        }
    }
}

@Composable
internal fun AudioKindLabel(kind: AudioSourceKind) {
    val labelRes = when (kind) {
        AudioSourceKind.PRE_RECORDED -> R.string.audio_kind_pre_recorded
        AudioSourceKind.PRE_GENERATED_TTS -> R.string.audio_kind_pre_generated_tts
    }
    Surface(
        shape = RoundedCornerShape(8.dp),
        color = MaterialTheme.colorScheme.primaryContainer,
        contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
    ) {
        Text(
            text = stringResource(labelRes),
            style = MaterialTheme.typography.labelLarge,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
        )
    }
}

@Composable
internal fun SectionLabel(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.titleMedium,
        color = MaterialTheme.colorScheme.onBackground,
    )
}

@Preview(showBackground = true, widthDp = 380, heightDp = 900)
@Composable
private fun TeacherModeScreenPreview() {
    TribalClassTheme(darkTheme = false) {
        TeacherModeScreen(onBack = {})
    }
}

@Preview(showBackground = true, widthDp = 380, heightDp = 900)
@Composable
private fun TeacherModeScreenDarkPreview() {
    TribalClassTheme(darkTheme = true) {
        TeacherModeScreen(onBack = {})
    }
}
