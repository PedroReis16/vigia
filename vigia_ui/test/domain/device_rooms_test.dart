import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/domain/enums/device_rooms.dart';

void main() {
  group('DeviceRoomsExtension', () {
    test('round-trips toApiString and fromString for defined rooms', () {
      final cases = {
        DeviceRooms.bedroom: 'Bedroom',
        DeviceRooms.livingRoom: 'LivingRoom',
        DeviceRooms.kitchen: 'Kitchen',
        DeviceRooms.bathroom: 'Bathroom',
        DeviceRooms.office: 'Office',
        DeviceRooms.garage: 'Garage',
        DeviceRooms.backyard: 'Backyard',
        DeviceRooms.frontyard: 'Frontyard',
      };

      for (final entry in cases.entries) {
        expect(entry.key.toApiString(), entry.value);
        expect(DeviceRoomsExtension.fromString(entry.value), entry.key);
      }
    });

    test('notDefined maps to null via toApiString', () {
      expect(DeviceRooms.notDefined.toApiString(), isNull);
    });

    test('fromString returns null for null, unknown, and notDefined', () {
      expect(DeviceRoomsExtension.fromString(null), isNull);
      expect(DeviceRoomsExtension.fromString('UnknownRoom'), isNull);
      expect(DeviceRoomsExtension.fromString('notDefined'), isNull);
    });
  });
}
