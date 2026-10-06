import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/domain/DTOs/device_identity.dart';

void main() {
  group('DeviceIdentity.fromJson', () {
    test('parses a valid payload', () {
      final identity = DeviceIdentity.fromJson({
        'device_id': 'ble-device-1',
        'name': 'Vigia Cam',
        'mac_address': 'AA:BB:CC:DD:EE:FF',
      });

      expect(identity.deviceId, 'ble-device-1');
      expect(identity.name, 'Vigia Cam');
      expect(identity.macAddress, 'AA:BB:CC:DD:EE:FF');
    });

    test('defaults name to Vigia when omitted', () {
      final identity = DeviceIdentity.fromJson({
        'device_id': 'ble-device-2',
        'mac_address': '11:22:33:44:55:66',
      });

      expect(identity.name, 'Vigia');
    });

    test('ignores legacy public keys', () {
      final identity = DeviceIdentity.fromJson({
        'device_id': 'ble-device-legacy',
        'sign_pub': 'sign-key',
        'ecdh_pub': 'ecdh-key',
        'name': 'Vigia Cam',
        'mac_address': 'AA:BB:CC:DD:EE:FF',
      });

      expect(identity.deviceId, 'ble-device-legacy');
      expect(identity.name, 'Vigia Cam');
    });

    test('throws FormatException for incomplete payload', () {
      expect(
        () => DeviceIdentity.fromJson({
          'device_id': 'ble-device-3',
        }),
        throwsA(isA<FormatException>()),
      );

      expect(
        () => DeviceIdentity.fromJson({
          'device_id': '',
          'mac_address': 'AA:BB:CC:DD:EE:FF',
        }),
        throwsA(isA<FormatException>()),
      );
    });
  });
}
