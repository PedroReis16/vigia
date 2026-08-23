import 'package:flutter/material.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:vigia_ui/data/services/whep_live_session.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/shared/widgets/app_loading_indicator.dart';

class DeviceVideoPlayer extends StatefulWidget {
  const DeviceVideoPlayer({
    super.key,
    required this.session,
    this.fullscreen = false,
    this.onToggleFullscreen,
    this.onRetry,
    this.heroTag,
  });

  final WhepLiveSession session;
  final bool fullscreen;
  final VoidCallback? onToggleFullscreen;
  final VoidCallback? onRetry;
  final Object? heroTag;

  @override
  State<DeviceVideoPlayer> createState() => _DeviceVideoPlayerState();
}

class _DeviceVideoPlayerState extends State<DeviceVideoPlayer> {
  bool _showControls = true;

  @override
  void initState() {
    super.initState();
    widget.session.addListener(_onSessionUpdate);
  }

  @override
  void didUpdateWidget(covariant DeviceVideoPlayer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.session != widget.session) {
      oldWidget.session.removeListener(_onSessionUpdate);
      widget.session.addListener(_onSessionUpdate);
    }
  }

  @override
  void dispose() {
    widget.session.removeListener(_onSessionUpdate);
    super.dispose();
  }

  void _onSessionUpdate() {
    if (mounted) setState(() {});
  }

  void _togglePlayPause() {
    if (widget.session.status != WhepLiveStatus.playing) return;
    widget.session.togglePause();
  }

  void _toggleControls() {
    setState(() => _showControls = !_showControls);
  }

  @override
  Widget build(BuildContext context) {
    final video = _buildVideo(context);
    final content = GestureDetector(
      onTap: _toggleControls,
      behavior: HitTestBehavior.opaque,
      child: Stack(
        fit: StackFit.expand,
        children: [video, if (_showControls) _buildControlsOverlay(context)],
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
      child: Material(type: MaterialType.transparency, child: content),
    );
  }

  Widget _buildVideo(BuildContext context) {
    final session = widget.session;

    if (session.status == WhepLiveStatus.connecting) {
      return ColoredBox(
        color: Colors.black,
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const AppLoadingIndicator(color: Colors.white),
              const SizedBox(height: 12),
              Text(
                context.translations.connectingTitle,
                style: const TextStyle(color: Colors.white70),
              ),
            ],
          ),
        ),
      );
    }

    if (session.status == WhepLiveStatus.error) {
      final message = session.errorMessage;
      return ColoredBox(
        color: Colors.black,
        child: Center(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  message == null
                      ? context.translations.connectionErrorFallback
                      : context.translations.errorWithMessage(message),
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.white70),
                ),
                if (widget.onRetry != null) ...[
                  const SizedBox(height: 12),
                  TextButton(
                    onPressed: widget.onRetry,
                    child: Text(context.translations.tryAgain),
                  ),
                ],
              ],
            ),
          ),
        ),
      );
    }

    return ColoredBox(
      color: Colors.black,
      child: RTCVideoView(
        session.renderer,
        objectFit: RTCVideoViewObjectFit.RTCVideoViewObjectFitCover,
      ),
    );
  }

  Widget _buildControlsOverlay(BuildContext context) {
    final session = widget.session;
    final canPlayPause = session.status == WhepLiveStatus.playing;
    final isPlaying = canPlayPause && !session.isPaused;

    return ColoredBox(
      color: Colors.black38,
      child: Stack(
        children: [
          if (canPlayPause)
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
                  widget.fullscreen ? Icons.fullscreen_exit : Icons.fullscreen,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
