import 'package:dio/dio.dart';
import 'package:vigia_ui/data/services/keycloak_auth_client.dart';
import 'package:vigia_ui/data/services/token_storage_service.dart';

class AuthInterceptor extends Interceptor {
  AuthInterceptor({
    required this._dio,
    required this._keycloak,
    required this._tokenStorage,
    required this._onRefreshFailed,
  });

  final Dio _dio;
  final KeycloakAuthClient _keycloak;
  final TokenStorageService _tokenStorage;
  final Future<void> Function() _onRefreshFailed;

  /// One refresh at a time. Successful calls stay parallel so a slow profile
  /// request cannot hold the device list in loading.
  Future<void>? _refreshing;

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _tokenStorage.getAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode != 401) {
      return handler.next(err);
    }

    if (err.requestOptions.extra['retried'] == true) {
      await _onRefreshFailed();
      return handler.next(err);
    }

    try {
      final refreshToken = await _tokenStorage.getRefreshToken();
      if (refreshToken == null || refreshToken.isEmpty) {
        await _onRefreshFailed();
        return handler.next(err);
      }

      await _refresh(refreshToken);

      final accessToken = await _tokenStorage.getAccessToken();
      final request = err.requestOptions;
      request.headers['Authorization'] = 'Bearer $accessToken';
      request.extra['retried'] = true;
      final retryResponse = await _dio.fetch(request);
      return handler.resolve(retryResponse);
    } catch (_) {
      await _onRefreshFailed();
      return handler.next(err);
    }
  }

  Future<void> _refresh(String refreshToken) {
    return _refreshing ??= _refreshAndSave(refreshToken).whenComplete(() {
      _refreshing = null;
    });
  }

  Future<void> _refreshAndSave(String refreshToken) async {
    final credentials = await _keycloak.refresh(refreshToken);
    await _tokenStorage.saveUserTokens(
      credentials.accessToken,
      credentials.refreshToken,
    );
  }
}
