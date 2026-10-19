import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:vigia_ui/domain/enums/clip_status.dart';
import 'package:vigia_ui/domain/plan/plan_view.dart';
import 'package:vigia_ui/domain/ui_models/device_clip_ui.dart';
import 'package:vigia_ui/l10n/app_localizations.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';

class DeviceClips extends StatefulWidget {
  const DeviceClips({
    super.key,
    required this.clips,
    required this.onPlay,
    this.playingId,
    this.interactive = true,
  });

  final List<DeviceClipUi> clips;
  final ValueChanged<DeviceClipUi> onPlay;
  final String? playingId;
  final bool interactive;

  @override
  State<DeviceClips> createState() => _DeviceClipsState();
}

class _DeviceClipsState extends State<DeviceClips> {
  final Set<String> _failedThumbs = {};

  @override
  Widget build(BuildContext context) {
    final t = context.translations;
    if (widget.clips.isEmpty) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 48),
        child: Center(
          child: Text(
            t.clipsEmpty,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
        ),
      );
    }

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        mainAxisSpacing: 12,
        crossAxisSpacing: 12,
        childAspectRatio: 0.72,
      ),
      itemCount: widget.clips.length,
      itemBuilder: (context, index) {
        final clip = widget.clips[index];
        return _ClipCard(
          clip: clip,
          selected: widget.playingId == clip.id,
          showThumb: !_failedThumbs.contains(clip.id),
          onThumbError: () {
            if (!mounted || _failedThumbs.contains(clip.id)) return;
            setState(() => _failedThumbs.add(clip.id));
          },
          onTap: widget.interactive && clip.isReady && clip.playbackUrl != null
              ? () => widget.onPlay(clip)
              : null,
        );
      },
    );
  }
}

class _ClipCard extends StatelessWidget {
  const _ClipCard({
    required this.clip,
    required this.selected,
    required this.showThumb,
    required this.onThumbError,
    required this.onTap,
  });

  final DeviceClipUi clip;
  final bool selected;
  final bool showThumb;
  final VoidCallback onThumbError;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final t = context.translations;
    final locale = Localizations.localeOf(context).languageCode;
    final createdAt = clip.createdAt;
    final when = createdAt == null
        ? ''
        : DateFormat.yMd(
            planLocale(locale),
          ).add_Hm().format(createdAt.toLocal());

    return Card(
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(
        borderRadius: const BorderRadius.all(Radius.circular(16)),
        side: BorderSide(
          color: selected
              ? theme.colorScheme.primary
              : theme.colorScheme.outlineVariant,
          width: selected ? 2 : 1,
        ),
      ),
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Expanded(
              child: _Thumbnail(
                clip: clip,
                show: showThumb,
                onError: onThumbError,
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    when,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: theme.textTheme.titleSmall,
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          clip.durationLabel ?? '',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ),
                      Text(
                        clipStatusLabel(t, clip.status),
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                      const SizedBox(width: 6),
                      DecoratedBox(
                        decoration: BoxDecoration(
                          color: clipStatusColor(clip.status),
                          shape: BoxShape.circle,
                        ),
                        child: const SizedBox(width: 8, height: 8),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Thumbnail extends StatelessWidget {
  const _Thumbnail({
    required this.clip,
    required this.show,
    required this.onError,
  });

  final DeviceClipUi clip;
  final bool show;
  final VoidCallback onError;

  @override
  Widget build(BuildContext context) {
    final placeholder = ColoredBox(
      color: Theme.of(context).colorScheme.surfaceContainerHighest,
      child: Icon(
        Icons.videocam_outlined,
        color: Theme.of(context).colorScheme.onSurfaceVariant,
      ),
    );
    final url = clip.thumbnailUrl;
    if (!show || url == null || url.isEmpty) return placeholder;

    return Image.network(
      url,
      fit: BoxFit.cover,
      errorBuilder: (context, error, stackTrace) {
        WidgetsBinding.instance.addPostFrameCallback((_) => onError());
        return placeholder;
      },
    );
  }
}

String clipStatusLabel(AppLocalizations t, ClipStatus status) {
  return switch (status) {
    ClipStatus.receiving => t.clipStatusReceiving,
    ClipStatus.assembling => t.clipStatusAssembling,
    ClipStatus.ready => t.clipStatusReady,
    ClipStatus.failed => t.clipStatusFailed,
  };
}

Color clipStatusColor(ClipStatus status) {
  return switch (status) {
    ClipStatus.ready => const Color(0xFF22C55E),
    ClipStatus.receiving || ClipStatus.assembling => const Color(0xFFF59E0B),
    ClipStatus.failed => const Color(0xFFEF4444),
  };
}
