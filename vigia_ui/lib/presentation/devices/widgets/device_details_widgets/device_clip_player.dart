import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import 'package:vigia_ui/presentation/shared/widgets/app_loading_indicator.dart';

class DeviceClipPlayer extends StatefulWidget {
  const DeviceClipPlayer({
    super.key,
    required this.url,
    this.posterUrl,
    this.onError,
  });

  final String url;
  final String? posterUrl;
  final VoidCallback? onError;

  @override
  State<DeviceClipPlayer> createState() => _DeviceClipPlayerState();
}

class _DeviceClipPlayerState extends State<DeviceClipPlayer> {
  VideoPlayerController? _controller;
  var _reportedError = false;
  var _playing = false;

  @override
  void initState() {
    super.initState();
    _open(widget.url);
  }

  @override
  void didUpdateWidget(covariant DeviceClipPlayer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.url != widget.url) {
      _reportedError = false;
      _playing = false;
      _disposeController();
      _open(widget.url);
    }
  }

  @override
  void dispose() {
    _disposeController();
    super.dispose();
  }

  void _open(String url) {
    final controller = VideoPlayerController.networkUrl(Uri.parse(url));
    _controller = controller;
    controller.addListener(_onTick);
    controller
        .initialize()
        .then((_) {
          if (!mounted || _controller != controller) return;
          setState(() {});
          controller.play();
        })
        .catchError((Object _) {
          _reportError();
        });
  }

  void _onTick() {
    final controller = _controller;
    if (!mounted || controller == null) return;
    if (controller.value.hasError) {
      _reportError();
      return;
    }

    final playing = controller.value.isPlaying;
    if (playing == _playing) return;
    setState(() => _playing = playing);
  }

  void _reportError() {
    if (_reportedError || !mounted) return;
    _reportedError = true;
    widget.onError?.call();
  }

  void _disposeController() {
    final controller = _controller;
    _controller = null;
    if (controller == null) return;
    controller.removeListener(_onTick);
    controller.dispose();
  }

  void _togglePlayback() {
    final controller = _controller;
    if (controller == null || !controller.value.isInitialized) return;
    if (controller.value.isPlaying) {
      controller.pause();
    } else {
      controller.play();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final controller = _controller;
    final ready = controller != null && controller.value.isInitialized;
    final aspectRatio = ready && controller.value.aspectRatio > 0
        ? controller.value.aspectRatio
        : 16 / 9;

    return DecoratedBox(
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: const BorderRadius.all(Radius.circular(16)),
        border: Border.all(color: theme.colorScheme.outlineVariant),
      ),
      child: ClipRRect(
        borderRadius: const BorderRadius.all(Radius.circular(16)),
        child: AspectRatio(
          aspectRatio: aspectRatio,
          child: Stack(
            fit: StackFit.expand,
            children: [
              if (ready)
                VideoPlayer(controller)
              else
                _Poster(url: widget.posterUrl),
              if (!ready)
                const Center(
                  child: AppLoadingIndicator(size: 28, strokeWidth: 2),
                ),
              if (ready)
                Align(
                  alignment: Alignment.bottomCenter,
                  child: ColoredBox(
                    color: theme.colorScheme.scrim.withValues(alpha: 0.45),
                    child: Row(
                      children: [
                        IconButton(
                          onPressed: _togglePlayback,
                          color: theme.colorScheme.onPrimary,
                          icon: Icon(
                            controller.value.isPlaying
                                ? Icons.pause
                                : Icons.play_arrow,
                          ),
                        ),
                        Expanded(
                          child: VideoProgressIndicator(
                            controller,
                            allowScrubbing: true,
                            colors: VideoProgressColors(
                              playedColor: theme.colorScheme.primary,
                              bufferedColor: theme.colorScheme.onPrimary
                                  .withValues(alpha: 0.35),
                              backgroundColor: theme.colorScheme.onPrimary
                                  .withValues(alpha: 0.2),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Poster extends StatelessWidget {
  const _Poster({required this.url});

  final String? url;

  @override
  Widget build(BuildContext context) {
    final fallback = ColoredBox(
      color: Theme.of(context).colorScheme.surfaceContainerHighest,
    );
    final poster = url;
    if (poster == null || poster.isEmpty) return fallback;

    return Image.network(
      poster,
      fit: BoxFit.cover,
      errorBuilder: (context, error, stackTrace) => fallback,
    );
  }
}
