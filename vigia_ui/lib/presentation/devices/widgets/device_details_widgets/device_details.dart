import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vigia_ui/domain/DTOs/device.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/devices/widgets/device_details_widgets/info_tile.dart';

class DeviceDetails extends ConsumerWidget {
  const DeviceDetails({super.key, required this.device});

  final Device device;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = context.translations;
    final theme = Theme.of(context);

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      children: [
        Text(device.nickname, style: theme.textTheme.headlineSmall),
        const SizedBox(height: 16),
        InfoTile(label: t.deviceNickname, value: device.nickname),
        if (device.room != null)
          InfoTile(label: t.deviceRoom, value: device.room.toString()),
        InfoTile(label: t.deviceIdLabel, value: device.id),
      ],
    );
  }
}
