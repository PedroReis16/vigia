import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/domain/DTOs/device_provision_config.dart';

void main() {
  test('lê a URL de ingestão retornada pela API', () {
    final config = DeviceProvisionConfig.fromJson({
      'fiwareApiKey': 'VIGIA',
      'streamIngestUrl': 'rtmps://ingest.example:8443',
    });

    expect(config.fiwareApiKey, 'VIGIA');
    expect(config.streamIngestUrl, 'rtmps://ingest.example:8443');
  });
}
