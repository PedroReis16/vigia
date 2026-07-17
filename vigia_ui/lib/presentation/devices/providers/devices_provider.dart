import 'package:flutter/services.dart' show rootBundle;
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:uuid/uuid.dart';
import 'package:vigia_ui/domain/DTOs/device.dart';

part 'devices_provider.g.dart';

@riverpod
Future<List<Device>> getDevices(Ref ref) async {
  try {
    final thumbnailData = await rootBundle.load('assets/images/fake_thumb.JPG');
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
    print(e);
    throw Exception('Failed to load devices');
  }
}
