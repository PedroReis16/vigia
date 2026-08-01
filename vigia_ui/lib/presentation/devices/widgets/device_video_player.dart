import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';

class DeviceVideoPlayer extends StatefulWidget {
  const DeviceVideoPlayer({
    super.key,
    required this.controller,
    this.fullscreen = false,
    this.onToggleFullscreen,
    this.heroTag,
  });

  final VideoPlayerController controller;
  final bool fullscreen;
  final VoidCallback? onToggleFullscreen;
  final Object? heroTag;

  @override
  State<DeviceVideoPlayer> createState() => _DeviceVideoPlayerState();
}

class _DeviceVideoPlayerState extends State<DeviceVideoPlayer> {
  bool _showControls = true;

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onControllerUpdate);
  }

  @override
  void didUpdateWidget(covariant DeviceVideoPlayer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.controller != widget.controller) {
      oldWidget.controller.removeListener(_onControllerUpdate);
      widget.controller.addListener(_onControllerUpdate);
    }
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onControllerUpdate);
    super.dispose();
  }

  void _onControllerUpdate() {
    if (mounted) setState(() {});
  }

  void _togglePlayPause() {
    final controller = widget.controller;
    if (!controller.value.isInitialized) return;
    if (controller.value.isPlaying) {
      controller.pause();
    } else {
      controller.play();
    }
  }

  void _toggleControls() {
    setState(() => _showControls = !_showControls);
  }

  @override
  Widget build(BuildContext context) {
    final video = _buildVideo();
    final content = GestureDetector(
      onTap: _toggleControls,
      behavior: HitTestBehavior.opaque,
      child: Stack(
        fit: StackFit.expand,
        children: [
          video,
          if (_showControls) _buildControlsOverlay(),
        ],
      ),
    );

    if (widget.heroTag == null) return content;

    return Hero(
      tag: widget.heroTag!,
      createRectTween: (begin, end) => RectTween(begin: begin, end: end),
      // Keep the lightweight thumbnail in flight — avoids hitching from the
      // video player / controls being composited in the Hero overlay.
      flightShuttleBuilder:
          (
            flightContext,
            animation,
            flightDirection,
            fromHeroContext,
            toHeroContext,
          ) {
            final Hero hero = flightDirection == HeroFlightDirection.push
                ? fromHeroContext.widget as Hero
                : toHeroContext.widget as Hero;
            return hero.child;
          },
      child: Material(
        type: MaterialType.transparency,
        child: content,
      ),
    );
  }

  Widget _buildVideo() {
    final controller = widget.controller;
    if (!controller.value.isInitialized) {
      return const ColoredBox(
        color: Colors.black,
        child: Center(child: CircularProgressIndicator()),
      );
    }

    return ColoredBox(
      color: Colors.black,
      child: FittedBox(
        fit: BoxFit.cover,
        child: SizedBox(
          width: controller.value.size.width,
          height: controller.value.size.height,
          child: VideoPlayer(controller),
        ),
      ),
    );
  }

  Widget _buildControlsOverlay() {
    final isPlaying = widget.controller.value.isPlaying;

    return ColoredBox(
      color: Colors.black38,
      child: Stack(
        children: [
          Center(
            child: IconButton(
              onPressed: _togglePlayPause,
              iconSize: 56,
              color: Colors.white,
              icon: Icon(
                isPlaying
                    ? Icons.pause_circle_filled
                    : Icons.play_circle_filled,
              ),
            ),
          ),
          if (widget.onToggleFullscreen != null)
            Positioned(
              right: 8,
              bottom: 8,
              child: IconButton(
                onPressed: widget.onToggleFullscreen,
                color: Colors.white,
                icon: Icon(
                  widget.fullscreen
                      ? Icons.fullscreen_exit
                      : Icons.fullscreen,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
