import 'package:dio/dio.dart';
import 'package:vigia_ui/data/services/keycloak_authorize.dart';
import 'package:vigia_ui/domain/DTOs/user_credentials.dart';
import 'package:vigia_ui/domain/exceptions/request_exception.dart';

class KeycloakAuthClient {
  KeycloakAuthClient(this._dio, {required this.realm, required this.clientId});

  final Dio _dio;
  final String realm;
  final String clientId;

  Future<UserCredentials> exchangeAuthorizationCode({
    required String code,
    required String codeVerifier,
  }) async {
    final data = await _post('/realms/$realm/protocol/openid-connect/token', {
      'grant_type': 'authorization_code',
      'client_id': clientId,
      'code': code,
      'redirect_uri': KeycloakAuthorize.redirectUri,
      'code_verifier': codeVerifier,
    });
    return _credentials(data);
  }

  Future<UserCredentials> refresh(String refreshToken) async {
    final data = await _post('/realms/$realm/protocol/openid-connect/token', {
      'grant_type': 'refresh_token',
      'client_id': clientId,
      'refresh_token': refreshToken,
    });
    return _credentials(data, fallbackRefresh: refreshToken);
  }

  Future<void> logout(String refreshToken) async {
    await _post('/realms/$realm/protocol/openid-connect/logout', {
      'client_id': clientId,
      'refresh_token': refreshToken,
    });
  }

  Future<Map<String, dynamic>> _post(
    String path,
    Map<String, String> body,
  ) async {
    final response = await _dio.post<Map<String, dynamic>>(
      path,
      data: body,
      options: Options(contentType: Headers.formUrlEncodedContentType),
    );
    return response.data ?? const {};
  }

  UserCredentials _credentials(
    Map<String, dynamic> data, {
    String? fallbackRefresh,
  }) {
    final access = data['access_token'];
    final refresh = data['refresh_token'] ?? fallbackRefresh;
    if (access is! String ||
        access.isEmpty ||
        refresh is! String ||
        refresh.isEmpty) {
      throw RequestException(message: 'Resposta de token do Keycloak inválida');
    }
    return UserCredentials(accessToken: access, refreshToken: refresh);
  }
}
