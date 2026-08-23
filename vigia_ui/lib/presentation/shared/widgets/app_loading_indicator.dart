import 'package:flutter/material.dart';

/// Branded Material spinner used on all platforms (no Cupertino adaptive).
class AppLoadingIndicator extends StatelessWidget {
  const AppLoadingIndicator({
    super.key,
    this.size,
    this.strokeWidth = 2.5,
    this.color,
  });

  /// Outer box size. When null, the indicator sizes itself (theme default).
  final double? size;

  final double strokeWidth;

  /// Defaults to [ProgressIndicatorTheme] / [ColorScheme.primary].
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final indicator = CircularProgressIndicator(
      strokeWidth: strokeWidth,
      color: color,
    );

    if (size == null) return indicator;

    return SizedBox(
      width: size,
      height: size,
      child: indicator,
    );
  }
}
