package com.tribalclass.ai.ui.teacher

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.unit.dp
import com.tribalclass.ai.R
import com.tribalclass.ai.data.IndicTrans2Provenance
import com.tribalclass.ai.data.IndicTrans2Result
import com.tribalclass.ai.data.SantaliAudioClip
import com.tribalclass.ai.data.TranslationStatus
import com.tribalclass.ai.speech.AsrState
import com.tribalclass.ai.ui.components.TranslationStatusLabel

/** Where the Hindi text of a run came from, so the screen labels it truthfully. */
enum class HindiSource { SPEECH, TYPED, PHRASE_BUTTON }

/** One run of the pipeline: the Hindi text, what IndicTrans2 returned for it, and the matching clip. */
data class HindiToSantaliRun(
    val hindi: String,
    val source: HindiSource,
    val translation: IndicTrans2Result?,
    val clip: SantaliAudioClip?,
)

/**
 * "Hindi → Santali Audio": Hindi speech → Hindi ASR → Hindi text → IndicTrans2 (text to text) →
 * Ol Chiki text → cached Santali WAV. Speech recognition, translation and playback are owned by the
 * screen; this only shows each step. When IndicTrans2 or the audio has nothing for a phrase, it says so.
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
internal fun HindiToSantaliAudioSection(
    asrState: AsrState,
    run: HindiToSantaliRun?,
    isPlaying: Boolean,
    canUseTypedText: Boolean,
    /** Test/demo buttons: the phrases the translation repository has output for. */
    phrases: List<String>,
    onRecordClick: () -> Unit,
    onUseTypedText: () -> Unit,
    onPhraseClick: (String) -> Unit,
    onPlayAgain: (SantaliAudioClip) -> Unit,
) {
    val colors = MaterialTheme.colorScheme
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        SectionLabel(stringResource(R.string.s2a_title))
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            color = colors.surfaceVariant,
        ) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text(
                    text = stringResource(R.string.s2a_description),
                    style = MaterialTheme.typography.bodyMedium,
                    color = colors.onSurfaceVariant,
                )
                SpeechInputControl(state = asrState, onClick = onRecordClick, idleLabelRes = R.string.s2a_start_recording)
                OutlinedButton(onClick = onUseTypedText, enabled = canUseTypedText) {
                    Text(stringResource(R.string.s2a_use_typed))
                }
                StepLabel(stringResource(R.string.s2a_try_phrase))
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    phrases.forEach { phrase ->
                        OutlinedButton(onClick = { onPhraseClick(phrase) }) { Text(phrase) }
                    }
                }
                if (run != null) RunSteps(run, isPlaying, onPlayAgain)
            }
        }
    }
}

@Composable
private fun RunSteps(run: HindiToSantaliRun, isPlaying: Boolean, onPlayAgain: (SantaliAudioClip) -> Unit) {
    val colors = MaterialTheme.colorScheme
    StepLabel(
        stringResource(
            when (run.source) {
                HindiSource.SPEECH -> R.string.s2a_hindi_from_speech
                HindiSource.TYPED -> R.string.s2a_hindi_typed
                HindiSource.PHRASE_BUTTON -> R.string.s2a_hindi_phrase_button
            },
        ),
    )
    Text(text = run.hindi, style = MaterialTheme.typography.headlineSmall, color = colors.onSurface)
    StepLabel(stringResource(R.string.s2a_indictrans2_step))
    val translation = run.translation
    if (translation == null) {
        Text(
            text = stringResource(R.string.s2a_not_available),
            style = MaterialTheme.typography.titleMedium,
            fontStyle = FontStyle.Italic,
            color = colors.onSurfaceVariant,
        )
        return
    }
    StepLabel(stringResource(R.string.s2a_santali_label))
    Text(text = translation.rawOutput, style = MaterialTheme.typography.headlineMedium, color = colors.onSurface)
    Text(
        text = stringResource(
            when (translation.provenance) {
                IndicTrans2Provenance.ON_DEVICE -> R.string.s2a_provenance_on_device
                IndicTrans2Provenance.RECORDED_DESKTOP_RUN -> R.string.s2a_provenance_recorded
            },
        ),
        style = MaterialTheme.typography.bodySmall,
        color = colors.onSurfaceVariant,
    )
    TranslationStatusLabel(TranslationStatus.MODEL_GENERATED_UNREVIEWED)
    StepLabel(stringResource(R.string.s2a_audio_step))
    if (run.clip == null) {
        // A documented translation without audio that passed the quality check: say so, play nothing.
        Text(
            text = stringResource(R.string.s2a_no_audio_for_phrase),
            style = MaterialTheme.typography.bodyMedium,
            fontStyle = FontStyle.Italic,
            color = colors.onSurfaceVariant,
        )
        return
    }
    if (isPlaying) {
        Text(text = stringResource(R.string.s2a_playing), style = MaterialTheme.typography.titleMedium, color = colors.primary)
    } else {
        OutlinedButton(onClick = { onPlayAgain(run.clip) }) { Text(stringResource(R.string.s2a_play_again)) }
    }
    AudioKindLabel(run.clip.kind)
}

@Composable
private fun StepLabel(text: String) {
    Text(text = text, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
}
