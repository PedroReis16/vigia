import 'package:dio/dio.dart';
import 'package:vigia_ui/data/services/keycloak_auth_client.dart';
import 'package:vigia_ui/domain/DTOs/user_credentials.dart';

class AuthRepository {
  AuthRepository(this._keycloak, this._dio);

  final KeycloakAuthClient _keycloak;
  final Dio _dio;

  Future<UserCredentials> exchangeAuthorizationCode({
    required String code,
    required String codeVerifier,
  }) {
    return _keycloak.exchangeAuthorizationCode(
      code: code,
      codeVerifier: codeVerifier,
    );
  }

  /// Revokes the Keycloak session via the API and soft-deletes [pushToken] when accepted.
  ///
  /// [accessToken] is optional so the caller can clear local storage first and
  /// still send a Bearer snapshot. [skipAuthRefresh] avoids a refresh loop after
  /// local logout.
  Future<void> logout({
    required String refreshToken,
    String? pushToken,
    String? accessToken,
  }) {
    return _dio.post(
      '/users/logout',
      data: {
        'refreshToken': refreshToken,
        if (pushToken != null && pushToken.isNotEmpty) 'pushToken': pushToken,
      },
      options: Options(
        headers: {
          if (accessToken != null && accessToken.isNotEmpty)
            'Authorization': 'Bearer $accessToken',
        },
        sendTimeout: const Duration(seconds: 5),
        receiveTimeout: const Duration(seconds: 5),
        extra: const {'skipAuthRefresh': true},
      ),
    );
  }
}
