package com.tribalclass.ai.ui.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.heightIn
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.tribalclass.ai.R
import com.tribalclass.ai.data.Lesson

/** "Lesson topic" chips for choosing one of the local lessons. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun LessonTopicSelector(lessons: List<Lesson>, selected: Lesson, onSelect: (Lesson) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(
            text = stringResource(R.string.teacher_topic_label),
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onBackground,
        )
        FlowRow(
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            lessons.forEach { lesson ->
                FilterChip(
                    selected = lesson.id == selected.id,
                    onClick = { onSelect(lesson) },
                    label = {
                        Text(
                            text = lesson.title,
                            style = MaterialTheme.typography.titleSmall,
                        )
                    },
                    modifier = Modifier.heightIn(min = 40.dp),
                )
            }
        }
    }
}
