package com.tribalclass.ai.navigation

import androidx.annotation.StringRes
import com.tribalclass.ai.R

/** Every top-level screen in the app. Screens not yet built route to a pending placeholder. */
enum class AppDestination(val route: String, @param:StringRes val titleRes: Int) {
    Home("home", R.string.app_name),
    Teacher("teacher", R.string.feature_teacher_title),
    Lessons("lessons", R.string.feature_lessons_title),
    Translation("translation", R.string.screen_translation_title),
    Worksheet("worksheet", R.string.feature_worksheets_title),
}
