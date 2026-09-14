import 'package:flutter/material.dart';
import 'package:vigia_ui/core/theme/app_assets.dart';
import 'package:vigia_ui/presentation/shell/vigia_logo_hero.dart';

/// Preloads logos + paints morph layers once so the first Auth↔Shell animation
/// does not pay image-decode / first-pipeline cost on device.
abstract final class AuthTransitionWarmUp {
  static bool _imagesReady = false;
  static bool _pipelinesPainted = false;

  static Future<void> precacheLogos(BuildContext context) async {
    if (_imagesReady) return;
    if (!context.mounted) return;

    final dpr = MediaQuery.devicePixelRatioOf(context);
    final authPx = (VigiaLogoHero.authHeight * dpr).round();
    final appBarPx = (VigiaLogoHero.appBarHeight * dpr).round();

    final providers = <ImageProvider>[
      for (final path in [AppAssets.dark.logo, AppAssets.light.logo]) ...[
        AssetImage(path),
        ResizeImage(AssetImage(path), width: authPx, height: authPx),
        ResizeImage(AssetImage(path), width: appBarPx, height: appBarPx),
      ],
    ];

    await Future.wait([
      for (final provider in providers) precacheImage(provider, context),
    ]);
    if (!context.mounted) return;
    _imagesReady = true;
  }

  /// Invisible on-screen paint so Impeller/Skia hit the same ops as the morph.
  static Widget? pipelinePrimer(BuildContext context) {
    if (_pipelinesPainted) return null;
    final colorScheme = Theme.of(context).colorScheme;
    final scaffoldBg = Theme.of(context).scaffoldBackgroundColor;

    return Positioned(
      // 1×1 slot; OverflowBox still paints full morph ops into the scene.
      left: 0,
      top: 0,
      width: 1,
      height: 1,
      child: IgnorePointer(
        child: Opacity(
          opacity: 0.002,
          child: OverflowBox(
            alignment: Alignment.topLeft,
            minWidth: 0,
            minHeight: 0,
            maxWidth: MediaQuery.sizeOf(context).width,
            maxHeight: MediaQuery.sizeOf(context).height,
            child: Stack(
              fit: StackFit.expand,
              children: [
                ColoredBox(color: colorScheme.primary),
                ColoredBox(color: scaffoldBg.withValues(alpha: 0.5)),
                Center(
                  child: VigiaLogoHero.image(height: VigiaLogoHero.authHeight),
                ),
                Center(
                  child: VigiaLogoHero.image(
                    height: VigiaLogoHero.appBarHeight,
                  ),
                ),
                const Opacity(
                  opacity: 0.5,
                  child: ColoredBox(color: Color(0xFF000000)),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  static void markPipelinesPainted() => _pipelinesPainted = true;
}
