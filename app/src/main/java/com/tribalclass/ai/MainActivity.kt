package com.tribalclass.ai

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.tribalclass.ai.navigation.AppNavHost
import com.tribalclass.ai.ui.theme.TribalClassTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            TribalClassTheme {
                AppNavHost()
            }
        }
    }
}
