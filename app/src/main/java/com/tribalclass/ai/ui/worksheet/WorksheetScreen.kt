package com.tribalclass.ai.ui.worksheet

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.pluralStringResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.tribalclass.ai.R
import com.tribalclass.ai.data.DemoLessons
import com.tribalclass.ai.data.PhrasePackTranslationRepository
import com.tribalclass.ai.data.TranslationEntry
import com.tribalclass.ai.data.TranslationRepository
import com.tribalclass.ai.data.Worksheet
import com.tribalclass.ai.data.WorksheetItem
import com.tribalclass.ai.ui.components.LessonTopicSelector
import com.tribalclass.ai.ui.components.StatusBadge
import com.tribalclass.ai.ui.components.TranslationStatusLabel
import com.tribalclass.ai.ui.theme.ReadyGreen
import com.tribalclass.ai.ui.theme.TribalClassTheme

/**
 * Bilingual worksheet for one local lesson. Every Santali word comes from the offline phrase
 * pack via [translator]; items without a stored translation are shown as unavailable.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WorksheetScreen(
    onBack: () -> Unit,
    translator: TranslationRepository = remember { PhrasePackTranslationRepository() },
) {
    // Same pattern as Teacher Mode: only the lesson id is saved and the lesson is looked up again.
    var selectedLessonId by rememberSaveable { mutableStateOf(DemoLessons.default.id) }
    val lesson = DemoLessons.byId(selectedLessonId)
    val worksheet = remember(lesson, translator) { Worksheet.build(lesson, translator) }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text(stringResource(R.string.worksheet_title)) },
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
                .padding(padding),
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
                LessonTopicSelector(
                    lessons = DemoLessons.all,
                    selected = lesson,
                    onSelect = { selectedLessonId = it.id },
                )
                WorksheetHeader(worksheet)
                WordsSection(worksheet)
                PracticeSection(worksheet)
                TeacherSection(worksheet)
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun WorksheetHeader(worksheet: Worksheet) {
    val colors = MaterialTheme.colorScheme
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        color = colors.primary,
        contentColor = colors.onPrimary,
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = worksheet.lesson.title,
                style = MaterialTheme.typography.headlineSmall,
            )
            Text(
                text = worksheet.lesson.description,
                style = MaterialTheme.typography.bodyLarge,
                color = colors.onPrimary.copy(alpha = 0.85f),
                modifier = Modifier.padding(top = 4.dp),
            )
            FlowRow(
                modifier = Modifier.padding(top = 14.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                HeaderTag(stringResource(R.string.teacher_language_pair))
                HeaderTag(stringResource(R.string.teacher_script))
                StatusBadge(label = stringResource(R.string.worksheet_offline), dotColor = ReadyGreen)
            }
        }
    }
}

@Composable
private fun HeaderTag(text: String) {
    Surface(
        shape = RoundedCornerShape(12.dp),
        color = MaterialTheme.colorScheme.secondaryContainer,
        contentColor = MaterialTheme.colorScheme.onSecondaryContainer,
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.labelLarge,
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
        )
    }
}

@Composable
private fun WordsSection(worksheet: Worksheet) {
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        SectionTitle(stringResource(R.string.worksheet_words_title))
        Text(
            text = pluralStringResource(
                R.plurals.worksheet_translated_count,
                worksheet.items.size,
                worksheet.translatedItems.size,
                worksheet.items.size,
            ),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        worksheet.items.forEach { WordCard(it) }
    }
}

@Composable
private fun WordCard(item: WorksheetItem) {
    val colors = MaterialTheme.colorScheme
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        color = colors.surfaceVariant,
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            LabelledText(label = stringResource(R.string.teacher_input_label)) {
                Text(
                    text = item.hindi,
                    style = MaterialTheme.typography.titleLarge,
                    color = colors.onSurface,
                )
            }
            LabelledText(label = stringResource(R.string.teacher_result_label)) {
                val translation = item.translation
                if (translation != null) {
                    Text(
                        text = translation.santaliOlChiki,
                        style = MaterialTheme.typography.headlineSmall,
                        color = colors.onSurface,
                    )
                    TranslationStatusLabel(translation.status, modifier = Modifier.padding(top = 4.dp))
                } else {
                    Text(
                        text = stringResource(R.string.worksheet_translation_not_available),
                        style = MaterialTheme.typography.bodyLarge,
                        fontStyle = FontStyle.Italic,
                        color = colors.onSurfaceVariant,
                    )
                }
            }
        }
    }
}

@Composable
private fun LabelledText(label: String, content: @Composable () -> Unit) {
    Column {
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        content()
    }
}

@Composable
private fun PracticeSection(worksheet: Worksheet) {
    val pairs = worksheet.translatedItems
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        SectionTitle(stringResource(R.string.worksheet_practice_title))
        when {
            pairs.size >= Worksheet.MIN_MATCHING_PAIRS -> MatchingActivity(worksheet)
            pairs.size == 1 -> ReadAloudActivity(pairs.single())
            else -> Text(
                text = stringResource(R.string.worksheet_practice_none),
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

/** Shown when a lesson has exactly one translated word, too few to match. */
@Composable
private fun ReadAloudActivity(entry: TranslationEntry) {
    val colors = MaterialTheme.colorScheme
    Text(
        text = stringResource(R.string.worksheet_practice_read_aloud),
        style = MaterialTheme.typography.bodyLarge,
        color = colors.onSurface,
    )
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        color = colors.tertiaryContainer,
        contentColor = colors.onTertiaryContainer,
    ) {
        Row(
            modifier = Modifier.padding(18.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Text(text = entry.hindi, style = MaterialTheme.typography.headlineSmall)
            Text(text = "→", style = MaterialTheme.typography.headlineSmall)
            Text(text = entry.santaliOlChiki, style = MaterialTheme.typography.headlineSmall)
        }
    }
}

private enum class MatchFeedback { None, Correct, TryAgain }

/**
 * Tap a Hindi word, then the Santali word that means the same. Matched pairs stay marked.
 * The Santali column order is fixed by [Worksheet.matchingSantaliOrder].
 */
@Composable
private fun MatchingActivity(worksheet: Worksheet) {
    val lessonId = worksheet.lesson.id
    // Keyed by lesson so switching lessons starts a fresh activity.
    var matched by rememberSaveable(lessonId) { mutableStateOf(ArrayList<String>()) }
    var selectedHindi by rememberSaveable(lessonId) { mutableStateOf<String?>(null) }
    var feedback by remember(lessonId) { mutableStateOf(MatchFeedback.None) }
    val allMatched = matched.size == worksheet.translatedItems.size

    Text(
        text = stringResource(R.string.worksheet_practice_match),
        style = MaterialTheme.typography.bodyLarge,
        color = MaterialTheme.colorScheme.onSurface,
    )
    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        Column(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            ColumnHeading(stringResource(R.string.teacher_input_label))
            worksheet.translatedItems.forEach { entry ->
                MatchTile(
                    text = entry.hindi,
                    matched = entry.hindi in matched,
                    selected = entry.hindi == selectedHindi,
                    onClick = {
                        selectedHindi = entry.hindi
                        feedback = MatchFeedback.None
                    },
                )
            }
        }
        Column(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            ColumnHeading(stringResource(R.string.teacher_script))
            worksheet.matchingSantaliOrder.forEach { entry ->
                MatchTile(
                    text = entry.santaliOlChiki,
                    matched = entry.hindi in matched,
                    selected = false,
                    onClick = {
                        val hindi = selectedHindi ?: return@MatchTile
                        if (hindi == entry.hindi) {
                            matched = ArrayList(matched + hindi)
                            feedback = MatchFeedback.Correct
                        } else {
                            feedback = MatchFeedback.TryAgain
                        }
                        selectedHindi = null
                    },
                )
            }
        }
    }
    val message = when {
        allMatched -> R.string.worksheet_match_all_done
        feedback == MatchFeedback.Correct -> R.string.worksheet_match_correct
        feedback == MatchFeedback.TryAgain -> R.string.worksheet_match_try_again
        selectedHindi != null -> R.string.worksheet_match_pick_santali
        else -> R.string.worksheet_match_pick_hindi
    }
    Text(
        text = stringResource(message),
        style = MaterialTheme.typography.titleMedium,
        color = if (feedback == MatchFeedback.TryAgain && !allMatched) {
            MaterialTheme.colorScheme.error
        } else {
            MaterialTheme.colorScheme.onSurface
        },
    )
    if (matched.isNotEmpty()) {
        OutlinedButton(
            onClick = {
                matched = ArrayList()
                selectedHindi = null
                feedback = MatchFeedback.None
            },
            modifier = Modifier.heightIn(min = 48.dp),
        ) {
            Text(stringResource(R.string.worksheet_match_restart))
        }
    }
}

@Composable
private fun ColumnHeading(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.labelLarge,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
}

@Composable
private fun MatchTile(text: String, matched: Boolean, selected: Boolean, onClick: () -> Unit) {
    val colors = MaterialTheme.colorScheme
    val container = when {
        matched -> colors.primaryContainer
        selected -> colors.secondaryContainer
        else -> colors.surfaceVariant
    }
    val content = when {
        matched -> colors.onPrimaryContainer
        selected -> colors.onSecondaryContainer
        else -> colors.onSurface
    }
    Surface(
        onClick = onClick,
        enabled = !matched,
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 64.dp),
        shape = RoundedCornerShape(16.dp),
        color = container,
        contentColor = content,
        border = if (selected) BorderStroke(2.dp, colors.secondary) else null,
    ) {
        Box(contentAlignment = Alignment.Center, modifier = Modifier.padding(12.dp)) {
            Text(text = text, style = MaterialTheme.typography.headlineSmall)
        }
    }
}

@Composable
private fun TeacherSection(worksheet: Worksheet) {
    val colors = MaterialTheme.colorScheme
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        SectionTitle(stringResource(R.string.worksheet_teacher_title))
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            color = colors.tertiaryContainer,
            contentColor = colors.onTertiaryContainer,
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Text(
                    text = stringResource(R.string.worksheet_teacher_instruction),
                    style = MaterialTheme.typography.bodyLarge,
                )
                Column {
                    Text(
                        text = stringResource(R.string.teacher_lesson_activity_label),
                        style = MaterialTheme.typography.labelLarge,
                    )
                    Text(
                        text = worksheet.lesson.activity,
                        style = MaterialTheme.typography.bodyLarge,
                        modifier = Modifier.padding(top = 2.dp),
                    )
                }
                Text(
                    text = stringResource(R.string.worksheet_teacher_review_note),
                    style = MaterialTheme.typography.bodyMedium,
                    fontStyle = FontStyle.Italic,
                )
            }
        }
    }
}

@Composable
private fun SectionTitle(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.titleLarge,
        color = MaterialTheme.colorScheme.onBackground,
    )
}

@Preview(showBackground = true, widthDp = 360, heightDp = 1400)
@Composable
private fun WorksheetScreenPreview() {
    TribalClassTheme(darkTheme = false) {
        WorksheetScreen(onBack = {})
    }
}
