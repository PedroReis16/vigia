import 'dart:ui' show lerpDouble;

import 'package:flutter/material.dart';

/// Morphs a full-screen primary veil into the AppBar (or vice-versa).
///
/// Login: the shell stays fully built underneath. A primary veil shrinks to the
/// AppBar and a soft body scrim dissolves last, so list/FAB/nav don't pop in.
/// Logout: the Auth page stays built underneath while the veil expands, then
/// dissolves to reveal the form.
class AuthToShellTransition extends StatelessWidget {
  const AuthToShellTransition({
    super.key,
    required this.animation,
    required this.child,
    this.reverse = false,
  });

  static const duration = Duration(milliseconds: 780);

  final Animation<double> animation;
  final Widget child;
  final bool reverse;

  @override
  Widget build(BuildContext context) {
    final curved = CurvedAnimation(
      parent: animation,
      curve: Curves.easeInOutCubic,
    );
    final colorScheme = Theme.of(context).colorScheme;
    final scaffoldBg = Theme.of(context).scaffoldBackgroundColor;
    final media = MediaQuery.of(context);
    final appBarHeight = media.padding.top + kToolbarHeight;
    final fullHeight = media.size.height;

    return AnimatedBuilder(
      animation: curved,
      builder: (context, _) {
        final t = curved.value;

        final barHeight = reverse
            ? lerpDouble(appBarHeight, fullHeight, t)!
            : lerpDouble(fullHeight, appBarHeight, t)!;

        // Primary veil stays solid while resizing, then softens away once it
        // matches the AppBar (login) / fills the screen (logout).
        final veilOpacity =
            1.0 -
            const Interval(0.82, 1.0, curve: Curves.easeOut).transform(t);

        // Covers body + bottom nav so devices spinner / FAB don't flash while
        // the bar is still morphing. Dissolves after the veil has settled.
        final bodyScrimOpacity = reverse
            ? 0.0
            : 1.0 -
                const Interval(0.62, 1.0, curve: Curves.easeOutCubic)
                    .transform(t);

        // On logout, hold Auth hidden until the veil has mostly expanded so
        // the form doesn't flash over the departing shell.
        final childOpacity = reverse
            ? const Interval(0.55, 0.95, curve: Curves.easeOut).transform(t)
            : 1.0;

        return Stack(
          fit: StackFit.expand,
          children: [
            Opacity(
              opacity: childOpacity.clamp(0.0, 1.0),
              child: child,
            ),
            if (bodyScrimOpacity > 0.001)
              Positioned(
                top: appBarHeight,
                left: 0,
                right: 0,
                bottom: 0,
                child: IgnorePointer(
                  child: Opacity(
                    opacity: bodyScrimOpacity.clamp(0.0, 1.0),
                    child: ColoredBox(color: scaffoldBg),
                  ),
                ),
              ),
            if (veilOpacity > 0.001)
              Positioned(
                top: 0,
                left: 0,
                right: 0,
                height: barHeight,
                child: IgnorePointer(
                  child: Opacity(
                    opacity: veilOpacity.clamp(0.0, 1.0),
                    child: ColoredBox(color: colorScheme.primary),
                  ),
                ),
              ),
          ],
        );
      },
    );
  }
}
