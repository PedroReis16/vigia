import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/domain/DTOs/device_identity.dart';

void main() {
  group('DeviceIdentity.fromJson', () {
    test('parses a valid payload', () {
      final identity = DeviceIdentity.fromJson({
        'device_id': 'ble-device-1',
        'sign_pub': 'sign-key',
        'ecdh_pub': 'ecdh-key',
        'name': 'Vigia Cam',
        'mac_address': 'AA:BB:CC:DD:EE:FF',
      });

      expect(identity.deviceId, 'ble-device-1');
      expect(identity.signPub, 'sign-key');
      expect(identity.ecdhPub, 'ecdh-key');
      expect(identity.name, 'Vigia Cam');
      expect(identity.macAddress, 'AA:BB:CC:DD:EE:FF');
    });

    test('defaults name to Vigia when omitted', () {
      final identity = DeviceIdentity.fromJson({
        'device_id': 'ble-device-2',
        'sign_pub': 'sign-key',
        'ecdh_pub': 'ecdh-key',
        'mac_address': '11:22:33:44:55:66',
      });

      expect(identity.name, 'Vigia');
    });

    test('throws FormatException for incomplete payload', () {
      expect(
        () => DeviceIdentity.fromJson({
          'device_id': 'ble-device-3',
          'sign_pub': 'sign-key',
        }),
        throwsA(isA<FormatException>()),
      );

      expect(
        () => DeviceIdentity.fromJson({
          'device_id': '',
          'sign_pub': 'sign-key',
          'ecdh_pub': 'ecdh-key',
          'mac_address': 'AA:BB:CC:DD:EE:FF',
        }),
        throwsA(isA<FormatException>()),
      );
    });
  });
}
