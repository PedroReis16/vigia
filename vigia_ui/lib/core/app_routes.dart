abstract final class AppRoutes {
  static const loginPage = '/login';

  static const registerPage = '/register';

  static const devicesPage = '/devices';

  static const deviceStreamRelative = ':deviceId';

  static const deviceStreamPage = '$devicesPage/:deviceId';

  static const settingsPage = '/settings';
}
