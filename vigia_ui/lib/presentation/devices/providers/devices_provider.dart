import 'package:flutter/services.dart' show rootBundle;
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:uuid/uuid.dart';
import 'package:vigia_ui/domain/DTOs/device.dart';

part 'devices_provider.g.dart';

@Riverpod(keepAlive: true)
class Devices extends _$Devices {
  @override
  Future<List<Device>> build() async {
    try {
      final thumbnailData = await rootBundle.load(
        'assets/images/fake_thumb.JPG',
      );
      final thumbnail = thumbnailData.buffer.asUint8List();
      return [
        Device(
          id: const Uuid().v4(),
          description: 'Device 1',
          thumbnail: thumbnail,
        ),
        Device(id: const Uuid().v4(), description: 'Device 2'),
        Device(id: const Uuid().v4(), description: 'Device 3'),
      ];
    } catch (e) {
      throw Exception('Failed to load devices');
    }
  }

  void addDevice(Device device) {
    final current = state.asData?.value ?? [];
    state = AsyncData([device, ...current]);
  }
}
