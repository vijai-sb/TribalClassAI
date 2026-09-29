package com.tribalclass.ai.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.tribalclass.ai.ui.home.HomeScreen
import com.tribalclass.ai.ui.pending.PendingScreen
import com.tribalclass.ai.ui.teacher.TeacherModeScreen
import com.tribalclass.ai.ui.worksheet.WorksheetScreen

@Composable
fun AppNavHost(navController: NavHostController = rememberNavController()) {
    NavHost(navController = navController, startDestination = AppDestination.Home.route) {
        composable(AppDestination.Home.route) {
            HomeScreen(onNavigate = { navController.navigate(it.route) })
        }

        composable(AppDestination.Teacher.route) {
            TeacherModeScreen(onBack = { navController.popBackStack() })
        }

        composable(AppDestination.Worksheet.route) {
            WorksheetScreen(onBack = { navController.popBackStack() })
        }

        // These routes exist so navigation is wired end to end,
        // but each screen is replaced by its real implementation in a later phase.
        listOf(
            AppDestination.Lessons,
            AppDestination.Translation,
        ).forEach { destination ->
            composable(destination.route) {
                PendingScreen(
                    titleRes = destination.titleRes,
                    onBack = { navController.popBackStack() },
                )
            }
        }
    }
}
