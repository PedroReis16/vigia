import 'package:flutter/material.dart';

extension ShowSnackbar on BuildContext {
  void showSnackbar({
    required String message,
    required Color color,
    Duration duration = const Duration(seconds: 2),
  }) {
    ScaffoldMessenger.of(this).showSnackBar(
      SnackBar(
        content: Align(
          alignment: Alignment.center,
          child: Text(
            message,
            style: const TextStyle(color: Colors.white),
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
