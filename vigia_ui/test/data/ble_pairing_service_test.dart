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

  group('BlePairingService.provisionPayload', () {
    test('includes the client certificate when registration returned one', () {
      final payload = BlePairingService.provisionPayload(
        ssid: 'casa',
        password: 'segredo',
        apiBaseUrl: 'https://services.vigiadeteccoes.com.br/vigia',
        fiwareApiKey: 'VIGIA',
        streamIngestUrl: 'rtmps://ingest.example/live',
        clientCert: 'CERT',
        clientKey: 'KEY',
      );

      expect(payload['client_cert'], 'CERT');
      expect(payload['client_key'], 'KEY');
    });

    test('omits the certificate fields when registration returned none', () {
      final payload = BlePairingService.provisionPayload(
        ssid: 'casa',
        password: 'segredo',
        apiBaseUrl: 'http://localhost/vigia',
        fiwareApiKey: 'VIGIA',
        streamIngestUrl: 'rtmp://localhost/live',
      );

      expect(payload.containsKey('client_cert'), isFalse);
      expect(payload.containsKey('client_key'), isFalse);
    });
  });
}
