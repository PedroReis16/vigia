import 'package:flutter/material.dart';

/// Color tokens for Vigia light and dark themes.
///
/// Prefer [Theme.of] `.colorScheme` for Material roles. Use
/// `Theme.of(context).extension<AppColors>()` for semantic colors
/// (success, info, warning) and direct token access.
@immutable
final class AppColors extends ThemeExtension<AppColors> {
  const AppColors({
    required this.primary,
    required this.primaryContainer,
    required this.secondary,
    required this.secondaryContainer,
    required this.background,
    required this.surface,
    required this.textPrimary,
    required this.textSecondary,
    required this.outline,
    required this.outlineVariant,
    required this.error,
    required this.success,
    required this.info,
    required this.warning,
  });

  final Color primary;
  final Color primaryContainer;
  final Color secondary;
  final Color secondaryContainer;
  final Color background;
  final Color surface;
  final Color textPrimary;
  final Color textSecondary;
  final Color outline;
  final Color outlineVariant;
  final Color error;
  final Color success;
  final Color info;
  final Color warning;

  static const light = AppColors(
    primary: Color(0xFF669CEE),
    primaryContainer: Color(0xFFE2E7EE),
    secondary: Color(0xFF68C19B),
    secondaryContainer: Color(0xFFEAF7F1),
    background: Color(0xFFFFF9F5),
    surface: Color(0xFFFFFFFF),
    textPrimary: Color(0xFF46526D),
    // ~60% visual weight of textPrimary on light surfaces
    textSecondary: Color(0xFF7A8499),
    outline: Color(0xFF9AA3B2),
    outlineVariant: Color(0xFFE2E7EE),
    error: Color(0xFFEF4444),
    success: Color(0xFF68C19B),
    info: Color(0xFF669CEE),
    warning: Color(0xFF9A5B00),
  );

  static const dark = AppColors(
    primary: Color(0xFF669CEE),
    primaryContainer: Color(0xFF2A3A55),
    secondary: Color(0xFF68C19B),
    secondaryContainer: Color(0xFF1E3D32),
    background: Color(0xFF12151C),
    surface: Color(0xFF1A1F2A),
    textPrimary: Color(0xFFF4F7FA),
    textSecondary: Color(0xFFA9B0BE),
    outline: Color(0xFF7A8499),
    outlineVariant: Color(0xFF2F3848),
    error: Color(0xFFFF6B6B),
    success: Color(0xFF68C19B),
    info: Color(0xFF669CEE),
    warning: Color(0xFFF6C85F),
  );

  ColorScheme toColorScheme(Brightness brightness) {
    // Light primary (#669CEE) is intentionally soft; white onPrimary keeps
    // filled buttons, FAB, and AppBar chrome on-brand with the auth scaffold.
    final onPrimary = brightness == Brightness.light
        ? const Color(0xFFFFFFFF)
        : background;
    final onSecondary = brightness == Brightness.light
        ? const Color(0xFFFFFFFF)
        : background;
    final onError = brightness == Brightness.light
        ? const Color(0xFFFFFFFF)
        : background;

    return ColorScheme(
      brightness: brightness,
      primary: primary,
      onPrimary: onPrimary,
      primaryContainer: primaryContainer,
      onPrimaryContainer: textPrimary,
      secondary: secondary,
      onSecondary: onSecondary,
      secondaryContainer: secondaryContainer,
      onSecondaryContainer: textPrimary,
      surface: surface,
      onSurface: textPrimary,
      onSurfaceVariant: textSecondary,
      error: error,
      onError: onError,
      outline: outline,
      outlineVariant: outlineVariant,
      surfaceContainerHighest: primaryContainer,
    );
  }

  @override
  AppColors copyWith({
    Color? primary,
    Color? primaryContainer,
    Color? secondary,
    Color? secondaryContainer,
    Color? background,
    Color? surface,
    Color? textPrimary,
    Color? textSecondary,
    Color? outline,
    Color? outlineVariant,
    Color? error,
    Color? success,
    Color? info,
    Color? warning,
  }) {
    return AppColors(
      primary: primary ?? this.primary,
      primaryContainer: primaryContainer ?? this.primaryContainer,
      secondary: secondary ?? this.secondary,
      secondaryContainer: secondaryContainer ?? this.secondaryContainer,
      background: background ?? this.background,
      surface: surface ?? this.surface,
      textPrimary: textPrimary ?? this.textPrimary,
      textSecondary: textSecondary ?? this.textSecondary,
      outline: outline ?? this.outline,
      outlineVariant: outlineVariant ?? this.outlineVariant,
      error: error ?? this.error,
      success: success ?? this.success,
      info: info ?? this.info,
      warning: warning ?? this.warning,
    );
  }

  @override
  AppColors lerp(ThemeExtension<AppColors>? other, double t) {
    if (other is! AppColors) return this;
    return AppColors(
      primary: Color.lerp(primary, other.primary, t)!,
      primaryContainer: Color.lerp(
        primaryContainer,
        other.primaryContainer,
        t,
      )!,
      secondary: Color.lerp(secondary, other.secondary, t)!,
      secondaryContainer: Color.lerp(
        secondaryContainer,
        other.secondaryContainer,
        t,
      )!,
      background: Color.lerp(background, other.background, t)!,
      surface: Color.lerp(surface, other.surface, t)!,
      textPrimary: Color.lerp(textPrimary, other.textPrimary, t)!,
      textSecondary: Color.lerp(textSecondary, other.textSecondary, t)!,
      outline: Color.lerp(outline, other.outline, t)!,
      outlineVariant: Color.lerp(outlineVariant, other.outlineVariant, t)!,
      error: Color.lerp(error, other.error, t)!,
      success: Color.lerp(success, other.success, t)!,
      info: Color.lerp(info, other.info, t)!,
      warning: Color.lerp(warning, other.warning, t)!,
    );
  }
}

extension AppColorsContext on BuildContext {
  AppColors get appColors => Theme.of(this).extension<AppColors>()!;
}
