package com.tribalclass.ai.data

/** The demo lessons shipped in the app. Everything here is on-device; nothing is fetched. */
object DemoLessons {
    val all: List<Lesson> = listOf(
        Lesson(
            id = "greetings",
            title = "Greetings",
            description = "Everyday phrases for starting the class and meeting each other.",
            hindiItems = listOf(
                "नमस्ते",
                "सुप्रभात",
                "आपका नाम क्या है?",
                "मेरा नाम ___ है।",
            ),
            activity = "Children stand in a circle. Each child greets the next one and says their own name using the phrases.",
        ),
        Lesson(
            id = "numbers_1_10",
            title = "Numbers 1–10",
            description = "Counting from one to ten.",
            hindiItems = listOf(
                "एक",
                "दो",
                "तीन",
                "चार",
                "पाँच",
                "छह",
                "सात",
                "आठ",
                "नौ",
                "दस",
            ),
            activity = "Count classroom items together, such as pencils or chairs, saying each number aloud.",
        ),
        Lesson(
            id = "classroom_objects",
            title = "Classroom Objects",
            description = "Names of things children see in the classroom.",
            hindiItems = listOf(
                "किताब",
                "पेंसिल",
                "कलम",
                "कुर्सी",
                "मेज़",
                "बैग",
                "दरवाज़ा",
                "खिड़की",
            ),
            activity = "The teacher says a word and children point to or touch that object in the room.",
        ),
    )

    val default: Lesson get() = all.first()

    fun byId(id: String): Lesson = all.firstOrNull { it.id == id } ?: default
}
