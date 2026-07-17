import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';

class VideoPreview extends StatelessWidget {
  const VideoPreview({required this.controller, super.key});

  final VideoPlayerController controller;

  @override
  Widget build(BuildContext context) {
    if (!controller.value.isInitialized) {
      return const SizedBox(
        height: 180,
        child: Center(child: CircularProgressIndicator()),
      );
    }

    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: AspectRatio(
        aspectRatio: controller.value.aspectRatio,
        child: VideoPlayer(controller),
      ),
    );
  }
}
