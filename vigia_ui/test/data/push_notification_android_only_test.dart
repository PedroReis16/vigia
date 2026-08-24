import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/data/services/push_notification_coordinator.dart';

void main() {
  test('push notifications are enabled only on Android', () {
    expect(arePushNotificationsEnabled, Platform.isAndroid);
  });
}
