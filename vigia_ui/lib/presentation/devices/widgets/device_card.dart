import 'package:flutter/material.dart';
import 'package:vigia_ui/core/theme/theme_colors.dart';
import 'package:vigia_ui/domain/enums/device_rooms.dart';
import 'package:vigia_ui/domain/environments.dart';
import 'package:vigia_ui/domain/ui_models/device_ui.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';

class DeviceCard extends StatelessWidget {
  final DeviceUIModel device;
  final VoidCallback? onTap;

  const DeviceCard({super.key, required this.device, this.onTap});

  @override
  Widget build(BuildContext context) {
    final thumbnail = device.thumbnailUrl;

    return GestureDetector(
      onTap: onTap?.call,
      child: Card(
        clipBehavior: Clip.antiAlias,
        child: AspectRatio(
          aspectRatio: 16 / 10,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(flex: 2, child: _buildThumbnail(context, thumbnail)),
              Expanded(
                flex: 1,
                child: Padding(
                  padding: const EdgeInsets.all(8),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        device.nickname ?? device.name,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      Row(
                        spacing: 4,
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          if (device.room != null)
                            Text(
                              _translateRoomName(context, device.room!),
                              style: TextStyle(color: Colors.grey.shade600),
                            ),
                          _buildRunningStatus(context, device.isRunning),
                        ],
                      ),
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

  Widget _buildThumbnail(BuildContext context, String? thumbnail) {
    Widget placeholder() => Container(
      color: Theme.of(context).colorScheme.surfaceContainerHighest,
      child: const Center(child: Icon(Icons.videocam_off_outlined)),
    );

    final child = thumbnail != null && thumbnail.isNotEmpty
        ? Image.network(
            "${Environments.apiUrl}/$thumbnail",
            fit: BoxFit.cover,
            errorBuilder: (context, error, stackTrace) => placeholder(),
          )
        : placeholder();

    // Skeleton placeholders omit [onTap] and must not share Hero tags.
    if (onTap == null) return child;

    return Hero(
      tag: 'device-thumb-${device.id}',
      createRectTween: (begin, end) => RectTween(begin: begin, end: end),
      child: Material(type: MaterialType.transparency, child: child),
    );
  }

  Widget _buildRunningStatus(BuildContext context, bool isRunning) {
    return Wrap(
      spacing: 4,
      runAlignment: WrapAlignment.center,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        Text(
          isRunning
              ? context.translations.online
              : context.translations.offline,
          style: TextStyle(color: Colors.grey.shade600),
        ),
        Icon(
          Icons.circle,
          color: isRunning
              ? context.appColors.success
              : context.appColors.error,
          size: 8,
        ),
      ],
    );
  }

  String _translateRoomName(BuildContext context, DeviceRooms room) {
    return switch (room) {
      DeviceRooms.livingRoom => context.translations.livingRoom,
      DeviceRooms.kitchen => context.translations.kitchen,
      DeviceRooms.bathroom => context.translations.bathroom,
      DeviceRooms.office => context.translations.office,
      DeviceRooms.garage => context.translations.garage,
      DeviceRooms.backyard => context.translations.backyard,
      DeviceRooms.frontyard => context.translations.frontyard,
      _ => context.translations.bedroom,
    };
  }
}
