import 'package:dio/dio.dart';
import 'package:vigia_ui/data/services/token_storage_service.dart';

class AuthInterceptor extends QueuedInterceptor {
  AuthInterceptor({
    required Dio dio,
    required Dio refreshDio,
    required TokenStorageService tokenStorage,
    required Future<void> Function() onRefreshFailed,
  }) : _dio = dio,
       _refreshDio = refreshDio,
       _tokenStorage = tokenStorage,
       _onRefreshFailed = onRefreshFailed;

  final Dio _dio;
  final Dio _refreshDio;
  final TokenStorageService _tokenStorage;
  final Future<void> Function() _onRefreshFailed;

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    if (_isPublicPath(options.path)) {
      return handler.next(options);
    }

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
    if (err.response?.statusCode != 401 ||
        _isPublicPath(err.requestOptions.path)) {
      return handler.next(err);
    }

    // Already retried once — avoid an infinite loop.
    if (err.requestOptions.extra['retried'] == true) {
      await _onRefreshFailed();
      return handler.next(err);
    }

    try {
      final refreshToken = await _tokenStorage.getRefreshToken();
      if (refreshToken == null) {
        await _onRefreshFailed();
        return handler.next(err);
      }

      final response = await _refreshDio.post(
        '/auth/refresh',
        data: {'refreshToken': refreshToken},
      );
      final newAccess = response.data['accessToken'] as String;
      final newRefresh = response.data['refreshToken'] as String;
      await _tokenStorage.saveUserTokens(newAccess, newRefresh);

      final request = err.requestOptions;
      request.headers['Authorization'] = 'Bearer $newAccess';
      request.extra['retried'] = true;
      final retryResponse = await _dio.fetch(request);
      return handler.resolve(retryResponse);
    } catch (_) {
      await _onRefreshFailed();
      return handler.next(err);
    }
  }

  bool _isPublicPath(String path) =>
      path.contains('/auth/login') ||
      path.contains('/auth/refresh') ||
      path.contains('/auth/register') ||
      path.contains('/auth/logout');
}
