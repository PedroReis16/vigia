import 'package:flutter/material.dart';
import 'package:vigia_ui/core/theme/app_assets.dart';

/// Shared logo sizes for Auth, AppBar, and the Auth↔Shell morph overlay.
///
/// Logo flight between Auth and Shell is drawn manually on the morph veil —
/// Flutter [Hero] is intentionally unused (placeholders flash on devices).
abstract final class VigiaLogoHero {
  static const authHeight = 300.0;
  static const appBarHeight = 40.0;

  /// Logo used on the primary-colored Auth / AppBar surfaces.
  static String get assetPath => AppAssets.dark.logo;

  /// Always decodes at [authHeight]; [FittedBox] scales for display.
  ///
  /// Animating [Image] width/height every frame forces re-layout / cache misses
  /// and causes a first-run flick on devices that later runs look fine.
  static Widget image({required double height}) {
    return SizedBox(
      height: height,
      width: height,
      child: FittedBox(
        fit: BoxFit.contain,
        child: Image.asset(
          assetPath,
          height: authHeight,
          width: authHeight,
          alignment: Alignment.center,
          filterQuality: FilterQuality.medium,
          gaplessPlayback: true,
        ),
      ),
    );
  }
}
