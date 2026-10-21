import 'package:flutter/material.dart';

class AppTheme {
  static const gold = Color(0xFFF0B429);
  static const goldDark = Color(0xFFD4900A);

  static ThemeData dark() => ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF111111),
        colorScheme: const ColorScheme.dark(
          primary: gold,
          secondary: gold,
          surface: Color(0xFF1C1C1C),
        ),
        cardTheme: const CardTheme(
          color: Color(0xFF1C1C1C),
          elevation: 0,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF111111),
          foregroundColor: Color(0xFFF0F0F0),
          elevation: 0,
        ),
        bottomNavigationBarTheme: const BottomNavigationBarThemeData(
          backgroundColor: Color(0xFF1C1C1C),
          selectedItemColor: gold,
          unselectedItemColor: Color(0xFF888888),
          type: BottomNavigationBarType.fixed,
        ),
        textTheme: const TextTheme(
          bodyMedium: TextStyle(color: Color(0xFFF0F0F0)),
          bodySmall: TextStyle(color: Color(0xFF888888)),
        ),
        useMaterial3: true,
      );

  static ThemeData light() => ThemeData(
        brightness: Brightness.light,
        scaffoldBackgroundColor: const Color(0xFFF5F5F5),
        colorScheme: const ColorScheme.light(
          primary: goldDark,
          secondary: goldDark,
          surface: Colors.white,
        ),
        cardTheme: const CardTheme(
          color: Colors.white,
          elevation: 0,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFFF5F5F5),
          foregroundColor: Color(0xFF111111),
          elevation: 0,
        ),
        bottomNavigationBarTheme: const BottomNavigationBarThemeData(
          backgroundColor: Colors.white,
          selectedItemColor: goldDark,
          unselectedItemColor: Color(0xFF555555),
          type: BottomNavigationBarType.fixed,
        ),
        textTheme: const TextTheme(
          bodyMedium: TextStyle(color: Color(0xFF111111)),
          bodySmall: TextStyle(color: Color(0xFF555555)),
        ),
        useMaterial3: true,
      );
}
