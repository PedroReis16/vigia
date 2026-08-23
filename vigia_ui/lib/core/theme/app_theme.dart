import 'package:flutter/cupertino.dart' show CupertinoPageTransitionsBuilder;
import 'package:flutter/material.dart';
import 'package:vigia_ui/core/theme/app_assets.dart';
import 'package:vigia_ui/core/theme/theme_colors.dart';

abstract final class AppTheme {
  static const _inputBorderRadius = BorderRadius.all(Radius.circular(10));
  static const _buttonBorderRadius = BorderRadius.all(Radius.circular(12));
  static const _cardBorderRadius = BorderRadius.all(Radius.circular(16));

  static ThemeData get light =>
      _build(AppColors.light, AppAssets.light, Brightness.light);

  static ThemeData get dark =>
      _build(AppColors.dark, AppAssets.dark, Brightness.dark);

  static ThemeData _build(
    AppColors colors,
    AppAssets assets,
    Brightness brightness,
  ) {
    final colorScheme = colors.toColorScheme(brightness);
    // Same primary as auth scaffold / morph veil so login → shell is seamless.
    final appBarBackground = colors.primary;
    final appBarForeground = colorScheme.onPrimary;

    final buttonStyle = ButtonStyle(
      backgroundColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.disabled)) {
          return colors.outlineVariant;
        }
        return colors.primary;
      }),
      foregroundColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.disabled)) {
          return colors.textSecondary;
        }
        return colorScheme.onPrimary;
      }),
      padding: const WidgetStatePropertyAll(
        EdgeInsets.symmetric(vertical: 14),
      ),
      shape: const WidgetStatePropertyAll(
        RoundedRectangleBorder(borderRadius: _buttonBorderRadius),
      ),
    );

    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: colors.background,
      extensions: [colors, assets],
      pageTransitionsTheme: const PageTransitionsTheme(
        builders: {
          TargetPlatform.android: CupertinoPageTransitionsBuilder(),
          TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
          TargetPlatform.macOS: CupertinoPageTransitionsBuilder(),
          TargetPlatform.linux: CupertinoPageTransitionsBuilder(),
          TargetPlatform.windows: CupertinoPageTransitionsBuilder(),
          TargetPlatform.fuchsia: CupertinoPageTransitionsBuilder(),
        },
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: appBarBackground,
        foregroundColor: appBarForeground,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: true,
        iconTheme: IconThemeData(color: appBarForeground),
        titleTextStyle: TextStyle(
          color: appBarForeground,
          fontSize: 20,
          fontWeight: FontWeight.w600,
        ),
      ),
      cardTheme: CardThemeData(
        color: colors.surface,
        elevation: 0,
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        shape: RoundedRectangleBorder(
          borderRadius: _cardBorderRadius,
          side: BorderSide(color: colors.outlineVariant),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: colors.primaryContainer,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 14,
          vertical: 12,
        ),
        border: OutlineInputBorder(
          borderRadius: _inputBorderRadius,
          borderSide: BorderSide(color: colors.outline),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: _inputBorderRadius,
          borderSide: BorderSide(color: colors.outline),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: _inputBorderRadius,
          borderSide: BorderSide(color: colors.primary, width: 1.5),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: _inputBorderRadius,
          borderSide: BorderSide(color: colors.error),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: _inputBorderRadius,
          borderSide: BorderSide(color: colors.error, width: 1.5),
        ),
        hintStyle: TextStyle(color: colors.textSecondary),
        labelStyle: TextStyle(color: colors.textSecondary),
      ),
      filledButtonTheme: FilledButtonThemeData(style: buttonStyle),
      elevatedButtonTheme: ElevatedButtonThemeData(style: buttonStyle),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: colors.textPrimary,
          side: BorderSide(color: colors.outline),
          padding: const EdgeInsets.symmetric(vertical: 14),
          shape: const RoundedRectangleBorder(
            borderRadius: _buttonBorderRadius,
          ),
        ),
      ),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: colors.primary,
        foregroundColor: colorScheme.onPrimary,
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return colors.surface;
          }
          return colors.outlineVariant;
        }),
        trackColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return colors.secondary;
          }
          return colors.primaryContainer;
        }),
        trackOutlineColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return colors.secondary;
          }
          return colors.outline;
        }),
      ),
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: colors.surface,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
      ),
      progressIndicatorTheme: ProgressIndicatorThemeData(color: colors.primary),
      dividerTheme: DividerThemeData(color: colors.outlineVariant),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: colors.textPrimary,
        contentTextStyle: TextStyle(
          color: brightness == Brightness.light
              ? colors.surface
              : colors.background,
        ),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        behavior: SnackBarBehavior.floating,
      ),
      textTheme: TextTheme(
        bodyLarge: TextStyle(color: colors.textPrimary),
        bodyMedium: TextStyle(color: colors.textPrimary),
        bodySmall: TextStyle(color: colors.textSecondary),
        titleLarge: TextStyle(
          color: colors.textPrimary,
          fontWeight: FontWeight.w700,
        ),
        titleMedium: TextStyle(
          color: colors.textPrimary,
          fontWeight: FontWeight.w600,
        ),
      ),
      datePickerTheme: DatePickerThemeData(
        backgroundColor: colors.surface,
        headerBackgroundColor: appBarBackground,
        headerForegroundColor: appBarForeground,
        dayForegroundColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return colorScheme.onPrimary;
          }
          return colors.textPrimary;
        }),
        dayBackgroundColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return colors.primary;
          }
          return null;
        }),
      ),
    );
  }
}
