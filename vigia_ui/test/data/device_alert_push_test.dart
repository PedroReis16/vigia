import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/data/services/push_notification_coordinator.dart';

void main() {
  test('fall and device offline payloads open the device', () {
    expect(
      deviceIdFromAlertData({'type': 'fall', 'deviceId': 'device-1'}),
      'device-1',
    );
    expect(
      deviceIdFromAlertData({'type': 'device_offline', 'deviceId': 'device-2'}),
      'device-2',
    );
    expect(deviceIdFromAlertData({'type': 'other', 'deviceId': 'device-1'}), isNull);
    expect(deviceIdFromAlertData({'type': 'device_offline'}), isNull);
  });
}
