import 'package:flutter/material.dart';

extension ShowSnackbar on BuildContext {
  void showSnackbar({
    required String message,
    required Color color,
    Duration duration = const Duration(seconds: 2),
  }) {
    final onColor = ThemeData.estimateBrightnessForColor(color) == Brightness.dark
        ? Colors.white
        : const Color(0xFF46526D);

    ScaffoldMessenger.of(this).showSnackBar(
      SnackBar(
        content: Align(
          alignment: Alignment.center,
          child: Text(
            message,
            style: TextStyle(color: onColor),
            textAlign: TextAlign.center,
          ),
        ),
        backgroundColor: color,
        behavior: SnackBarBehavior.fixed,
        duration: duration,
      ),
    );
  }
}
