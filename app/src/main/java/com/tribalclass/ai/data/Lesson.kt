package com.tribalclass.ai.data

/**
 * One classroom lesson bundled with the app. Content is Hindi only; Santali versions
 * will be added once they can be sourced and checked.
 */
data class Lesson(
    val id: String,
    val title: String,
    val description: String,
    val hindiItems: List<String>,
    val activity: String,
)
