package com.tribalclass.ai.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val LightColors = lightColorScheme(
    primary = SalGreen,
    onPrimary = Cream,
    primaryContainer = SalGreenContainer,
    onPrimaryContainer = SalGreenDeep,
    secondary = Palash,
    onSecondary = Cream,
    secondaryContainer = PalashContainer,
    onSecondaryContainer = PalashDeep,
    tertiary = Ochre,
    onTertiary = Cream,
    tertiaryContainer = OchreContainer,
    onTertiaryContainer = OchreDeep,
    background = Cream,
    onBackground = Ink,
    surface = Cream,
    onSurface = Ink,
    surfaceVariant = CreamVariant,
    onSurfaceVariant = InkMuted,
    outline = Outline,
)

private val DarkColors = darkColorScheme(
    primary = SalGreenLight,
    onPrimary = SalGreenDeep,
    primaryContainer = SalGreen,
    onPrimaryContainer = SalGreenContainer,
    secondary = PalashLight,
    onSecondary = PalashDeep,
    secondaryContainer = Palash,
    onSecondaryContainer = PalashContainer,
    tertiary = OchreLight,
    onTertiary = OchreDeep,
    tertiaryContainer = Ochre,
    onTertiaryContainer = OchreContainer,
    background = Night,
    onBackground = Paper,
    surface = Night,
    onSurface = Paper,
    surfaceVariant = NightVariant,
    onSurfaceVariant = PaperMuted,
    outline = Outline,
)

/** Fixed brand palette; dynamic (wallpaper) colour is intentionally not used. */
@Composable
fun TribalClassTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        typography = AppTypography,
        content = content,
    )
}
