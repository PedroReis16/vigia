import 'package:flutter/material.dart';

@immutable
class AppAssets extends ThemeExtension<AppAssets> {
  final String logo;

  const AppAssets({required this.logo});

  static const light = AppAssets(logo: "assets/images/vigia_logo.png");
  static const dark = AppAssets(logo: "assets/images/vigia_logo_dark.png");

  @override
  AppAssets copyWith({String? logo}) {
    return AppAssets(logo: logo ?? this.logo);
  }

  @override
  AppAssets lerp(ThemeExtension<AppAssets>? other, double t) {
    if (other is! AppAssets) return this;
    return t < 0.5 ? this : other;
  }
}
