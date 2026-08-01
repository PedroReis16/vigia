abstract final class AppRoutes {
  static const authPage = '/auth';

  static const devicesPage = '/devices';

  static const deviceDetailsRelative = ':deviceId';

  static const deviceDetailsPage = '$devicesPage/:deviceId';

  static const settingsPage = '/settings';
}
