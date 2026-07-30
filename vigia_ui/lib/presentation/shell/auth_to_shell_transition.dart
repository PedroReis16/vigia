import 'dart:ui' show lerpDouble;

import 'package:flutter/material.dart';
import 'package:vigia_ui/presentation/shell/vigia_logo_hero.dart';

/// Morphs a full-screen primary veil into the AppBar (or vice-versa).
///
/// Login: the shell stays fully built underneath. A primary veil shrinks to the
/// AppBar; an opaque body scrim covers list/FAB/nav until the bar settles.
/// Logout: an opaque veil expands from the AppBar while the logo flies on it;
/// Auth stays painted underneath (not [Offstage]) so the logo/forms decode
/// before the veil drops — otherwise devices show empty primary, then pop-in.
///
/// When [flyLogo] is true, the logo is drawn on the veil — avoiding Flutter
/// Hero, whose placeholders flash shell widgets on physical devices (Impeller).
///
/// Solid overlays intentionally avoid [Opacity] (saveLayer per frame).
class AuthToShellTransition extends StatelessWidget {
  const AuthToShellTransition({
    super.key,
    required this.animation,
    required this.child,
    this.reverse = false,
    this.flyLogo = false,
    this.logoFromCenter = false,
  });

  static const duration = Duration(milliseconds: 780);

  final Animation<double> animation;
  final Widget child;
  final bool reverse;
  final bool flyLogo;

  /// Enter: centered cold-start origin. Ignored on logout (AppBar → form top).
  final bool logoFromCenter;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final scaffoldBg = Theme.of(context).scaffoldBackgroundColor;
    final media = MediaQuery.of(context);
    final appBarHeight = media.padding.top + kToolbarHeight;
    final fullHeight = media.size.height;

    return AnimatedBuilder(
      animation: animation,
      child: RepaintBoundary(child: child),
      builder: (context, cachedChild) {
        final t = Curves.easeInOutCubic.transform(animation.value);

        final barHeight = reverse
            ? lerpDouble(appBarHeight, fullHeight, t)!
            : lerpDouble(fullHeight, appBarHeight, t)!;

        // Opaque veil until settled — no alpha fade (Impeller handoff flash).
        final showVeil = t < 0.98;

        final bodyScrimAlpha = reverse
            ? 0.0
            : 1.0 -
                const Interval(0.62, 0.92, curve: Curves.easeOutCubic)
                    .transform(t);

        // Logout: keep Auth painting from frame 0 (decode logo/forms under the
        // veil). Reveal only once the veil covers the screen — never Offstage.
        final showAuthUnderVeil = !reverse || t >= 0.82;

        Widget? logoFlight;
        if (flyLogo && showVeil) {
          final double logoH;
          final double logoTop;
          final endTopAppBar =
              media.padding.top +
              (kToolbarHeight - VigiaLogoHero.appBarHeight) / 2;
          final formTop = media.padding.top;
          final centerTop =
              media.padding.top +
              ((fullHeight -
                          media.padding.vertical -
                          VigiaLogoHero.authHeight) /
                      2)
                  .clamp(0.0, double.infinity);

          if (reverse) {
            // AppBar logo → auth form logo while the bar expands.
            logoH = lerpDouble(
              VigiaLogoHero.appBarHeight,
              VigiaLogoHero.authHeight,
              t,
            )!;
            logoTop = lerpDouble(endTopAppBar, formTop, t)!;
          } else {
            logoH = lerpDouble(
              VigiaLogoHero.authHeight,
              VigiaLogoHero.appBarHeight,
              t,
            )!;
            final startTop = logoFromCenter ? centerTop : formTop;
            logoTop = lerpDouble(startTop, endTopAppBar, t)!;
          }

          logoFlight = Positioned(
            top: logoTop,
            left: 0,
            right: 0,
            child: IgnorePointer(
              child: Center(
                child: VigiaLogoHero.image(height: logoH),
              ),
            ),
          );
        }

        final Widget shellLayer;
        if (showAuthUnderVeil) {
          shellLayer = cachedChild!;
        } else {
          // Opacity 0 still paints → Image decode / layout happen under veil.
          shellLayer = Opacity(opacity: 0, child: cachedChild);
        }

        return Stack(
          fit: StackFit.expand,
          children: [
            shellLayer,
            if (bodyScrimAlpha > 0.001)
              Positioned(
                top: appBarHeight,
                left: 0,
                right: 0,
                bottom: 0,
                child: IgnorePointer(
                  child: ColoredBox(
                    color: scaffoldBg.withValues(alpha: bodyScrimAlpha),
                  ),
                ),
              ),
            if (showVeil)
              Positioned(
                top: 0,
                left: 0,
                right: 0,
                height: barHeight,
                child: IgnorePointer(
                  child: ColoredBox(color: colorScheme.primary),
                ),
              ),
            ?logoFlight,
          ],
        );
      },
    );
  }
}
