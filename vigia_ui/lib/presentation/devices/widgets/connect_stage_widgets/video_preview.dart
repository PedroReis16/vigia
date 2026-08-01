import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';

class VideoPreview extends StatelessWidget {
  const VideoPreview({required this.controller, super.key});

  final VideoPlayerController controller;

  static const _borderRadius = BorderRadius.all(Radius.circular(16));

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    if (!controller.value.isInitialized) {
      return Container(
        height: 180,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: colorScheme.primaryContainer,
          borderRadius: _borderRadius,
          border: Border.all(color: colorScheme.outlineVariant),
        ),
        child: const CircularProgressIndicator(strokeWidth: 2),
      );
    }

    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: _borderRadius,
        border: Border.all(color: colorScheme.outlineVariant),
      ),
      child: ClipRRect(
        borderRadius: _borderRadius,
        child: AspectRatio(
          aspectRatio: controller.value.aspectRatio,
          child: VideoPlayer(controller),
        ),
      ),
    );
  }
}
