import 'package:dio/dio.dart';

class PushTokenRepository {
  final Dio _dio;

  PushTokenRepository(this._dio);

  Future<void> upsertToken(String token, String platform) async {
    await _dio.put(
      '/users/push-token',
      data: {'token': token, 'platform': platform},
    );
  }

  Future<void> deleteToken(String token) async {
    await _dio.delete('/users/push-token', data: {'token': token});
  }
}
