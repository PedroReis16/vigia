import 'package:vigia_ui/core/app_routes.dart';

/// Parses invite codes from public HTTPS landings and internal deep links.
abstract final class InviteDeepLink {
  static String? extractToken(Uri uri) {
    // Public landing: https://host/.../i/{code}
    final httpsCode = _codeFromPublicPath(uri);
    if (httpsCode != null) return httpsCode;

    // vigia://invite/{code}
    if (uri.scheme == 'vigia' && uri.host == 'invite') {
      if (uri.pathSegments.isNotEmpty) {
        return uri.pathSegments.first;
      }
      final path = uri.path.replaceFirst('/', '');
      return path.isEmpty ? null : path;
    }

    // vigia:///invite/{code}
    if (uri.scheme == 'vigia' &&
        uri.pathSegments.length >= 2 &&
        uri.pathSegments.first == 'invite') {
      return uri.pathSegments[1];
    }

    // In-app path: /invite/{code}
    if (uri.pathSegments.length >= 2 && uri.pathSegments.first == 'invite') {
      return uri.pathSegments[1];
    }

    // Platform may surface "//invite/{code}" after stripping the scheme.
    if (uri.host == 'invite' && uri.pathSegments.isNotEmpty) {
      return uri.pathSegments.first;
    }

    return null;
  }

  static String? inviteLocationFromUri(Uri uri) {
    final token = extractToken(uri);
    if (token == null || token.isEmpty) return null;
    return AppRoutes.invitePagePath(token);
  }

  static String? _codeFromPublicPath(Uri uri) {
    if (uri.scheme != 'http' && uri.scheme != 'https') return null;

    final segments = uri.pathSegments.where((s) => s.isNotEmpty).toList();
    final iIndex = segments.lastIndexOf('i');
    if (iIndex >= 0 && iIndex + 1 < segments.length) {
      final code = segments[iIndex + 1];
      return code.isEmpty ? null : code;
    }
    return null;
  }
}
