import 'package:dio/dio.dart';
import 'package:vigia_ui/domain/DTOs/user_credentials.dart';
import 'package:vigia_ui/domain/exceptions/request_exception.dart';
import 'package:vigia_ui/domain/exceptions/unauthroized_exception.dart';

class AuthRepository {
  final Dio _dio;
  AuthRepository(this._dio);

  Future<UserCredentials> login(String email, String password) async {
    final response = await _dio.post(
      '/auth/login',
      data: {'email': email, 'password': password},
    );

    switch (response.statusCode) {
      case 200:
        return UserCredentials(
          accessToken: response.data['accessToken'],
          refreshToken: response.data['refreshToken'],
        );
      case 401:
        throw UnauthorizedException('Credenciais inválidas');
      default:
        throw RequestException('Erro ao fazer login: ${response.statusCode}');
    }
  }

  Future<void> logout(String refreshToken) async {
    final response = await _dio.post(
      '/auth/logout',
      data: {'refreshToken': refreshToken},
    );

    if (response.statusCode == 200) {
      return;
    }
    throw Exception('Failed to logout');
  }
}
