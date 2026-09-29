package com.tribalclass.ai.ui.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.tribalclass.ai.R
import com.tribalclass.ai.navigation.AppDestination
import com.tribalclass.ai.ui.components.FeatureCard
import com.tribalclass.ai.ui.components.StatusBadge
import com.tribalclass.ai.ui.theme.ReadyGreen
import com.tribalclass.ai.ui.theme.TribalClassTheme

@Composable
fun HomeScreen(onNavigate: (AppDestination) -> Unit) {
    val colors = MaterialTheme.colorScheme
    Surface(modifier = Modifier.fillMaxSize(), color = colors.background) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .safeDrawingPadding(),
            contentAlignment = Alignment.TopCenter,
        ) {
            Column(
                modifier = Modifier
                    .widthIn(max = 640.dp)
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 20.dp, vertical = 16.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp),
            ) {
                HomeHeader()
                Spacer(Modifier.height(4.dp))
                FeatureCard(
                    title = stringResource(R.string.feature_teacher_title),
                    description = stringResource(R.string.feature_teacher_body),
                    iconRes = R.drawable.ic_teacher,
                    accent = colors.primary,
                    onAccent = colors.onPrimary,
                    onClick = { onNavigate(AppDestination.Teacher) },
                )
                FeatureCard(
                    title = stringResource(R.string.feature_lessons_title),
                    description = stringResource(R.string.feature_lessons_body),
                    iconRes = R.drawable.ic_lessons,
                    accent = colors.secondary,
                    onAccent = colors.onSecondary,
                    onClick = { onNavigate(AppDestination.Lessons) },
                )
                FeatureCard(
                    title = stringResource(R.string.feature_worksheets_title),
                    description = stringResource(R.string.feature_worksheets_body),
                    iconRes = R.drawable.ic_worksheet,
                    accent = colors.tertiary,
                    onAccent = colors.onTertiary,
                    onClick = { onNavigate(AppDestination.Worksheet) },
                )
            }
        }
    }
}

@Composable
private fun HomeHeader() {
    val colors = MaterialTheme.colorScheme
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(28.dp),
        color = colors.primary,
        contentColor = colors.onPrimary,
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                StatusBadge(
                    label = stringResource(R.string.home_status_offline),
                    dotColor = ReadyGreen,
                    containerColor = colors.surface,
                    contentColor = colors.onSurface,
                )
            }
            Spacer(Modifier.height(12.dp))
            Text(
                text = stringResource(R.string.app_name),
                style = MaterialTheme.typography.displaySmall,
            )
            Text(
                text = stringResource(R.string.home_subtitle),
                style = MaterialTheme.typography.titleMedium,
                color = colors.onPrimary.copy(alpha = 0.85f),
                modifier = Modifier.padding(top = 4.dp),
            )
            Spacer(Modifier.height(20.dp))
            Text(
                text = stringResource(R.string.home_target_language_label).uppercase(),
                style = MaterialTheme.typography.labelMedium,
                color = colors.onPrimary.copy(alpha = 0.7f),
            )
            Surface(
                modifier = Modifier.padding(top = 6.dp),
                shape = RoundedCornerShape(12.dp),
                color = colors.secondaryContainer,
                contentColor = colors.onSecondaryContainer,
            ) {
                Text(
                    text = stringResource(R.string.home_target_language),
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp),
                )
            }
        }
    }
}

@Preview(showBackground = true, widthDp = 380, heightDp = 780)
@Composable
private fun HomeScreenPreview() {
    TribalClassTheme(darkTheme = false) {
        HomeScreen(onNavigate = {})
    }
}

@Preview(showBackground = true, widthDp = 380, heightDp = 780)
@Composable
private fun HomeScreenDarkPreview() {
    TribalClassTheme(darkTheme = true) {
        HomeScreen(onNavigate = {})
    }
}
