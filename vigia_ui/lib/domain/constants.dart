import 'package:flutter_blue_plus/flutter_blue_plus.dart';

class Constants {
  /// Matches [SERVICE_UUID] in vigia-fall/integration/device_ble.py
  static final Guid serviceConnectionUuid = Guid(
    'adbb2064-403f-490f-8e0b-d2df7a3e8976',
  );
  static final Guid charIdentityUuid = Guid(
    '776ee4be-ecd4-4331-9f0e-7a53f1d9a4ba',
  );
  static final Guid charChallengeUuid = Guid(
    '2984802e-d12e-4e6c-870f-3b37f1845961',
  );
  static final Guid charProvisionUuid = Guid(
    '2562213c-2180-4320-a70f-247a6125b47a',
  );

  /// Matches [helpers_create_device_name] in vigia-fall/shared/helpers.py
  static const String deviceNamePrefix = 'Vigia-';

  /// Placeholder until real API bind exists.
  static const String localDevApiToken = 'local-dev';
}
