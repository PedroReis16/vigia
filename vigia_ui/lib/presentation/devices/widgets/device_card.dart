import 'package:flutter/material.dart';
import 'package:vigia_ui/domain/DTOs/device.dart';
import 'package:vigia_ui/domain/environments.dart';

class DeviceCard extends StatelessWidget {
  final Device device;
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
              Expanded(
                flex: 2,
                child: _buildThumbnail(context, thumbnail),
              ),
              Expanded(
                flex: 1,
                child: Padding(
                  padding: const EdgeInsets.all(8),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        device.nickname,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      if (device.room != null)
                        Text(
                          device.room.toString(),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
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
    final child = thumbnail != null && thumbnail.isNotEmpty
        ? Image.network(
            "${Environments.apiUrl}/$thumbnail",
            fit: BoxFit.cover,
          )
        : Container(
            color: Theme.of(context).colorScheme.surfaceContainerHighest,
            child: const Center(
              child: Icon(Icons.videocam_off_outlined),
            ),
          );

    // Skeleton placeholders omit [onTap] and must not share Hero tags.
    if (onTap == null) return child;

    return Hero(
      tag: 'device-thumb-${device.id}',
      createRectTween: (begin, end) => RectTween(begin: begin, end: end),
      child: Material(
        type: MaterialType.transparency,
        child: child,
      ),
    );
  }
}
