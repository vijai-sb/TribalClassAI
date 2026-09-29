package com.tribalclass.ai.ui.components

import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.tribalclass.ai.R
import com.tribalclass.ai.data.TranslationStatus

/** Provenance of a shown translation, so unreviewed model output is never mistaken for checked text. */
@Composable
fun TranslationStatusLabel(status: TranslationStatus, modifier: Modifier = Modifier) {
    val colors = MaterialTheme.colorScheme
    val (labelRes, container, content) = when (status) {
        TranslationStatus.HUMAN_VERIFIED ->
            Triple(R.string.translation_status_human_verified, colors.primaryContainer, colors.onPrimaryContainer)
        TranslationStatus.MODEL_GENERATED_UNREVIEWED ->
            Triple(R.string.translation_status_model_unreviewed, colors.tertiaryContainer, colors.onTertiaryContainer)
    }
    Surface(modifier = modifier, shape = RoundedCornerShape(8.dp), color = container, contentColor = content) {
        Text(
            text = stringResource(labelRes),
            style = MaterialTheme.typography.labelLarge,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
        )
    }
}
