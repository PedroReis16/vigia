import 'dart:convert';
import 'dart:math';

import 'package:crypto/crypto.dart';

/// Authorization Code + PKCE pieces shared by the login sheet and tests.
abstract final class KeycloakAuthorize {
  static const redirectUri = 'vigia://auth/callback';
  static const scopes = 'openid offline_access';

  static Uri build({
    required String baseUrl,
    required String realm,
    required String clientId,
    required String codeChallenge,
    required String state,
  }) {
    final root = baseUrl.endsWith('/')
        ? baseUrl.substring(0, baseUrl.length - 1)
        : baseUrl;
    return Uri.parse(
      '$root/realms/$realm/protocol/openid-connect/auth',
    ).replace(
      queryParameters: {
        'client_id': clientId,
        'redirect_uri': redirectUri,
        'response_type': 'code',
        'scope': scopes,
        'code_challenge': codeChallenge,
        'code_challenge_method': 'S256',
        'state': state,
      },
    );
  }
}

abstract final class Pkce {
  static String verifier({Random? random}) {
    final source = random ?? Random.secure();
    final bytes = List<int>.generate(32, (_) => source.nextInt(256));
    return _base64Url(bytes);
  }

  static String challengeFor(String verifier) {
    final digest = sha256.convert(utf8.encode(verifier));
    return _base64Url(digest.bytes);
  }

  static String _base64Url(List<int> bytes) =>
      base64Url.encode(bytes).replaceAll('=', '');
}

class KeycloakCallback {
  const KeycloakCallback({this.code, this.error, this.state});

  final String? code;
  final String? error;
  final String? state;

  bool get isSuccess => error == null && code != null && code!.isNotEmpty;

  static bool isCallback(Uri uri) {
    return uri.scheme == 'vigia' &&
        uri.host == 'auth' &&
        (uri.path == '/callback' || uri.path == 'callback');
  }

  static KeycloakCallback? tryParse(Uri uri) {
    if (!isCallback(uri)) return null;
    return KeycloakCallback(
      code: _blankToNull(uri.queryParameters['code']),
      error: _blankToNull(uri.queryParameters['error']),
      state: _blankToNull(uri.queryParameters['state']),
    );
  }

  static String? _blankToNull(String? value) {
    if (value == null || value.isEmpty) return null;
    return value;
  }
}
