import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:skeletonizer/skeletonizer.dart';
import 'package:vigia_ui/domain/enums/clip_status.dart';
import 'package:vigia_ui/domain/ui_models/device_clip_ui.dart';
import 'package:vigia_ui/domain/ui_models/device_ui.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/devices/providers/device_clips_provider.dart';
import 'package:vigia_ui/presentation/devices/providers/devices_provider.dart';
import 'package:vigia_ui/presentation/devices/widgets/device_details_widgets/device_clip_player.dart';
import 'package:vigia_ui/presentation/devices/widgets/device_details_widgets/device_clips.dart';

class DeviceClipsPage extends ConsumerStatefulWidget {
  const DeviceClipsPage({super.key, required this.deviceId});

  final String deviceId;

  @override
  ConsumerState<DeviceClipsPage> createState() => _DeviceClipsPageState();
}

class _DeviceClipsPageState extends ConsumerState<DeviceClipsPage> {
  String? _playingId;
  String? _videoUrl;
  String? _posterUrl;
  var _videoError = false;

  DeviceUIModel? _device() {
    final devices = ref.watch(devicesProvider).asData?.value;
    if (devices == null) return null;
    for (final device in devices) {
      if (device.id == widget.deviceId) return device;
    }
    return null;
  }

  void _play(DeviceClipUi clip) {
    final playbackUrl = clip.playbackUrl;
    if (!clip.isReady || playbackUrl == null) return;
    if (_playingId == clip.id && _videoUrl == playbackUrl && !_videoError) {
      return;
    }

    setState(() {
      _playingId = clip.id;
      _videoUrl = playbackUrl;
      _posterUrl = clip.thumbnailUrl;
      _videoError = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final t = context.translations;
    final theme = Theme.of(context);
    final device = _device();
    final nickname = device?.nickname?.trim();
    final displayName = device == null
        ? null
        : (nickname != null && nickname.isNotEmpty)
        ? nickname
        : device.name;
    final clips = ref.watch(deviceClipsListProvider(widget.deviceId));

    return Scaffold(
      appBar: AppBar(
        toolbarHeight: displayName == null ? null : 72,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(t.clips),
            if (displayName != null)
              Text(
                displayName,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onPrimary.withValues(alpha: 0.85),
                ),
              ),
          ],
        ),
      ),
      body: clips.when(
        loading: () => const _ClipsSkeleton(),
        error: (error, stackTrace) => _ClipsError(
          onRetry: () {
            ref
                .read(deviceClipsListProvider(widget.deviceId).notifier)
                .refresh();
          },
        ),
        data: (items) => ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
          children: [
            if (device != null && !device.isClipsEnabled)
              Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Text(
                  t.clipsStorageOffNotice,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ),
            if (_videoUrl != null) ...[
              DeviceClipPlayer(
                key: ValueKey(_videoUrl),
                url: _videoUrl!,
                posterUrl: _posterUrl,
                onError: () {
                  if (!mounted) return;
                  setState(() => _videoError = true);
                },
              ),
              const SizedBox(height: 12),
            ],
            if (_videoError)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text(
                  t.clipsPlayError,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.error,
                  ),
                ),
              ),
            DeviceClips(clips: items, playingId: _playingId, onPlay: _play),
          ],
        ),
      ),
    );
  }
}

class _ClipsError extends StatelessWidget {
  const _ClipsError({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final t = context.translations;
    final theme = Theme.of(context);

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              t.clipsLoadError,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyLarge,
            ),
            const SizedBox(height: 16),
            TextButton(onPressed: onRetry, child: Text(t.tryAgain)),
          ],
        ),
      ),
    );
  }
}

class _ClipsSkeleton extends StatelessWidget {
  const _ClipsSkeleton();

  @override
  Widget build(BuildContext context) {
    final placeholders = List<DeviceClipUi>.generate(
      4,
      (index) => DeviceClipUi(
        id: 'skeleton-$index',
        deviceId: '',
        status: ClipStatus.ready,
        frameCount: 90,
        fps: 30,
        createdAt: DateTime.utc(2026, 10, 6, 15, 4),
      ),
    );

    return Skeletonizer(
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        children: [
          DeviceClips(clips: placeholders, interactive: false, onPlay: (_) {}),
        ],
      ),
    );
  }
}
