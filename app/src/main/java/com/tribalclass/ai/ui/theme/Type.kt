package com.tribalclass.ai.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.font.FontWeight

private val Base = Typography()

// Slightly heavier headings and larger body text for classroom readability.
internal val AppTypography = Typography(
    displaySmall = Base.displaySmall.copy(fontWeight = FontWeight.Bold),
    headlineMedium = Base.headlineMedium.copy(fontWeight = FontWeight.Bold),
    titleLarge = Base.titleLarge.copy(fontWeight = FontWeight.SemiBold),
    titleMedium = Base.titleMedium.copy(fontWeight = FontWeight.SemiBold),
    bodyLarge = Base.bodyLarge,
    bodyMedium = Base.bodyMedium,
    labelLarge = Base.labelLarge.copy(fontWeight = FontWeight.SemiBold),
)
