import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/data/services/ble_pairing_service.dart';

void main() {
  group('BlePairingService.requiresLocationForBle', () {
    test('requires location on Android 11 and below', () {
      expect(BlePairingService.requiresLocationForBle(30), isTrue);
      expect(BlePairingService.requiresLocationForBle(29), isTrue);
    });

    test('does not require location on Android 12 and above', () {
      expect(BlePairingService.requiresLocationForBle(31), isFalse);
      expect(BlePairingService.requiresLocationForBle(35), isFalse);
    });
  });
}
