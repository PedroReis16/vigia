abstract final class AppRoutes {
  static const authPage = '/auth';

  static const devicesPage = '/devices';

  static const deviceDetailsRelative = ':deviceId';

  static const deviceDetailsPage = '$devicesPage/:deviceId';

  static const deviceClipsRelative = 'clips';

  static const deviceClipsPage = '$deviceDetailsPage/$deviceClipsRelative';

  static const settingsPage = '/settings';

  static const invitePage = '/invite/:token';

  static String invitePagePath(String token) => '/invite/$token';
}
