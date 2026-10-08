import 'package:vigia_ui/data/services/keycloak_auth_client.dart';
import 'package:vigia_ui/domain/DTOs/user_credentials.dart';

class AuthRepository {
  AuthRepository(this._keycloak);

  final KeycloakAuthClient _keycloak;

  Future<UserCredentials> exchangeAuthorizationCode({
    required String code,
    required String codeVerifier,
  }) {
    return _keycloak.exchangeAuthorizationCode(
      code: code,
      codeVerifier: codeVerifier,
    );
  }

  Future<void> logout(String refreshToken) {
    return _keycloak.logout(refreshToken);
  }
}
