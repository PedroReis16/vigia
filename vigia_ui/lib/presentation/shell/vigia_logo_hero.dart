import 'package:flutter/material.dart';
import 'package:vigia_ui/core/theme/app_assets.dart';

/// Shared [Hero] tag and sizes for the Vigia logo across Auth and AppBar.
abstract final class VigiaLogoHero {
  static const tag = 'vigia-logo';
  static const authHeight = 300.0;
  static const appBarHeight = 40.0;

  /// Logo used on the primary-colored Auth / AppBar surfaces.
  static String get assetPath => AppAssets.dark.logo;

  static Widget image({required double height}) {
    return Image.asset(
      assetPath,
      height: height,
      alignment: Alignment.center,
    );
  }
}
