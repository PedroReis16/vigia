import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/domain/DTOs/device.dart';
import 'package:vigia_ui/domain/enums/device_rooms.dart';

void main() {
  group('Device.fromJson', () {
    test('parses required and optional fields', () {
      final device = Device.fromJson({
        'id': 'dev-1',
        'name': 'Camera',
        'nickname': 'Sala',
        'ownerId': 'user-1',
        'thumbnailUrl': 'https://cdn.example/thumb.jpg',
        'room': 'LivingRoom',
        'isRunning': true,
        'isClipsEnabled': true,
      });

      expect(device.id, 'dev-1');
      expect(device.name, 'Camera');
      expect(device.nickname, 'Sala');
      expect(device.ownerId, 'user-1');
      expect(device.thumbnailUrl, 'https://cdn.example/thumb.jpg');
      expect(device.room, DeviceRooms.livingRoom);
      expect(device.isRunning, isTrue);
      expect(device.isClipsEnabled, isTrue);
    });

    test('applies defaults when optional fields are missing', () {
      final device = Device.fromJson({
        'id': 42,
        'ownerId': 7,
      });

      expect(device.id, '42');
      expect(device.name, '');
      expect(device.nickname, isNull);
      expect(device.ownerId, '7');
      expect(device.thumbnailUrl, isNull);
      expect(device.room, isNull);
      expect(device.isRunning, isFalse);
      expect(device.isClipsEnabled, isFalse);
    });

    test('maps unknown room string to null', () {
      final device = Device.fromJson({
        'id': 'dev-2',
        'name': 'Cam',
        'ownerId': 'user-2',
        'room': 'Attic',
      });

      expect(device.room, isNull);
    });
  });
}
