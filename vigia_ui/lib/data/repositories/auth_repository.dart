import 'package:dio/dio.dart';
import 'package:vigia_ui/domain/DTOs/user_credentials.dart';
import 'package:vigia_ui/domain/enums/error_codes.dart';
import 'package:vigia_ui/domain/exceptions/request_exception.dart';
import 'package:vigia_ui/domain/exceptions/unauthroized_exception.dart';

class AuthRepository {
  final Dio _dio;
  AuthRepository(this._dio);

  Future<UserCredentials> login(String email, String password) async {
    try {
      final response = await _dio.post(
        '/auth/login',
        data: {'email': email, 'password': password},
      );

      if (response.statusCode != 200) {
        throw RequestException(
          message: 'Erro ao fazer login: ${response.statusCode}',
        );
      }

      return UserCredentials(
        accessToken: response.data['accessToken'],
        refreshToken: response.data['refreshToken'],
      );
    } on DioException catch (requestException) {
      if (requestException.response?.statusCode == 401) {
        throw UnauthorizedException('Credenciais inválidas');
      }

      final data = requestException.response?.data;
      final code = ErrorCodes.values.firstWhere(
        (el) => el.value == data?['ErrorCode'],
        orElse: () => ErrorCodes.unknownError,
      );

      throw RequestException(
        message:
            'Erro ao fazer login: ${requestException.response?.statusCode}',
        errorCode: code,
      );
    }
  }

  Future<void> logout(String refreshToken) async {
    final response = await _dio.post(
      '/auth/logout',
      data: {'refreshToken': refreshToken},
    );

    if (response.statusCode != 200) {
      throw RequestException(
        message: 'Erro ao fazer logout: ${response.statusCode}',
      );
    }
  }

  Future<UserCredentials> register(
    String name,
    String email,
    String password,
  ) async {
    try {
      final response = await _dio.post(
        '/auth/register',
        data: {'name': name, 'email': email, 'password': password},
      );

      if (response.statusCode != 201) {
        throw RequestException(
          message: 'Erro ao registrar usuário: ${response.statusCode}',
          errorCode: ErrorCodes.unknownError,
        );
      }

      return UserCredentials(
        accessToken: response.data['accessToken'],
        refreshToken: response.data['refreshToken'],
      );
    } on DioException catch (requestException) {
      final data = requestException.response?.data;
      final code = ErrorCodes.values.firstWhere(
        (el) => el.value == data?['ErrorCode'],
        orElse: () => ErrorCodes.unknownError,
      );
      throw RequestException(
        message:
            'Erro ao registrar usuário: ${requestException.response?.statusCode}',
        errorCode: code,
      );
    }
  }
}
