import 'package:vigia_ui/core/theme/theme_colors.dart';
import 'package:flutter/material.dart';

abstract final class AppTheme {
  static const _inputBorderRadius = BorderRadius.all(Radius.circular(10));
  static const _buttonBorderRadius = BorderRadius.all(Radius.circular(12));
  static const _cardBorderRadius = BorderRadius.all(Radius.circular(16));

  static ThemeData get light {
    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: ThemeColors.background,
      colorScheme: ColorScheme.light(
        primary: ThemeColors.accent,
        onPrimary: Colors.white,
        secondary: ThemeColors.border,
        onSecondary: ThemeColors.label,
        surface: ThemeColors.cardBackground,
        onSurface: ThemeColors.label,
        error: Colors.red.shade400,
        onError: Colors.white,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: ThemeColors.background,
        foregroundColor: ThemeColors.label,
        elevation: 0,
        scrolledUnderElevation: 0,
        iconTheme: IconThemeData(color: ThemeColors.label),
        titleTextStyle: TextStyle(
          color: ThemeColors.label,
          fontSize: 20,
          fontWeight: FontWeight.w600,
        ),
      ),
      cardTheme: const CardThemeData(
        color: ThemeColors.cardBackground,
        elevation: 0,
        margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        shape: RoundedRectangleBorder(
          borderRadius: _cardBorderRadius,
          side: BorderSide(color: ThemeColors.border),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: ThemeColors.fieldBackground,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 14,
          vertical: 12,
        ),
        border: const OutlineInputBorder(
          borderRadius: _inputBorderRadius,
          borderSide: BorderSide(color: ThemeColors.border),
        ),
        enabledBorder: const OutlineInputBorder(
          borderRadius: _inputBorderRadius,
          borderSide: BorderSide(color: ThemeColors.border),
        ),
        focusedBorder: const OutlineInputBorder(
          borderRadius: _inputBorderRadius,
          borderSide: BorderSide(color: ThemeColors.accent, width: 1.5),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: _inputBorderRadius,
          borderSide: BorderSide(color: Colors.red.shade400),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: _inputBorderRadius,
          borderSide: BorderSide(color: Colors.red.shade400, width: 1.5),
        ),
        hintStyle: const TextStyle(color: ThemeColors.hint),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: ThemeColors.accent,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 14),
          shape: const RoundedRectangleBorder(
            borderRadius: _buttonBorderRadius,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: ThemeColors.label,
          side: const BorderSide(color: ThemeColors.border),
          padding: const EdgeInsets.symmetric(vertical: 14),
          shape: const RoundedRectangleBorder(
            borderRadius: _buttonBorderRadius,
          ),
        ),
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: ThemeColors.accent,
        foregroundColor: Colors.white,
      ),
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: ThemeColors.background,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
      ),
      progressIndicatorTheme: const ProgressIndicatorThemeData(
        color: ThemeColors.accent,
      ),
      dividerTheme: const DividerThemeData(color: ThemeColors.border),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: ThemeColors.label,
        contentTextStyle: const TextStyle(color: Colors.white),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        behavior: SnackBarBehavior.floating,
      ),
      textTheme: const TextTheme(
        bodyLarge: TextStyle(color: ThemeColors.label),
        bodyMedium: TextStyle(color: ThemeColors.label),
        bodySmall: TextStyle(color: ThemeColors.hint),
        titleLarge: TextStyle(
          color: ThemeColors.label,
          fontWeight: FontWeight.w700,
        ),
        titleMedium: TextStyle(
          color: ThemeColors.label,
          fontWeight: FontWeight.w600,
        ),
      ),
      datePickerTheme: DatePickerThemeData(
        backgroundColor: ThemeColors.background,
        headerBackgroundColor: ThemeColors.accent,
        headerForegroundColor: Colors.white,
        dayForegroundColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) return Colors.white;
          return ThemeColors.label;
        }),
        dayBackgroundColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return ThemeColors.accent;
          }
          return null;
        }),
      ),
    );
  }
}
