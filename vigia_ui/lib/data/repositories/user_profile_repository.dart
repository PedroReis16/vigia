import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:vigia_ui/domain/DTOs/user_profile.dart';
import 'package:vigia_ui/domain/api_asset_url.dart';
import 'package:vigia_ui/domain/enums/error_codes.dart';
import 'package:vigia_ui/domain/exceptions/request_exception.dart';
import 'package:vigia_ui/domain/exceptions/unauthroized_exception.dart';

class UserProfileRepository {
  UserProfileRepository(this.dio);

  final Dio dio;

  static const _users = '/users';

  Future<UserProfile> getProfile() async {
    try {
      final response = await dio.get('$_users/me');
      return _profileFrom(response.data);
    } on DioException catch (error) {
      throw _asException(error, 'Não foi possível carregar o perfil.');
    }
  }

  Future<UserProfile> uploadPicture(
    Uint8List bytes,
    String filename,
    String contentType,
  ) async {
    try {
      final body = FormData.fromMap({
        'file': MultipartFile.fromBytes(
          bytes,
          filename: filename,
          contentType: DioMediaType.parse(contentType),
        ),
      });
      final response = await dio.put('$_users/me/picture', data: body);
      return _profileFrom(response.data);
    } on DioException catch (error) {
      throw _asException(error, 'Não foi possível atualizar a foto.');
    }
  }

  Future<UserProfile> removePicture() async {
    try {
      final response = await dio.delete('$_users/me/picture');
      return _profileFrom(response.data);
    } on DioException catch (error) {
      throw _asException(error, 'Não foi possível atualizar a foto.');
    }
  }

  UserProfile _profileFrom(Object? data) {
    if (data is! Map) {
      throw RequestException(message: 'Resposta de perfil inválida.');
    }
    final profile = UserProfile.fromJson(Map<String, dynamic>.from(data));
    return UserProfile(
      id: profile.id,
      name: profile.name,
      firstName: profile.firstName,
      lastName: profile.lastName,
      email: profile.email,
      phone: profile.phone,
      pictureUrl: resolveApiAssetUrl(profile.pictureUrl),
    );
  }

  Exception _asException(DioException error, String fallback) {
    if (error.response?.statusCode == 401) {
      return UnauthorizedException('Permissões insuficientes.');
    }

    return RequestException(
      message: _message(error) ?? fallback,
      errorCode: _errorCode(error),
    );
  }

  String? _message(DioException error) {
    final data = error.response?.data;
    if (data is! Map) return null;
    final message = data['errorMessage'] ?? data['ErrorMessage'];
    return message is String && message.isNotEmpty ? message : null;
  }

  ErrorCodes _errorCode(DioException error) {
    final data = error.response?.data;
    if (data is! Map) return ErrorCodes.unknownError;
    final raw = data['errorCode'] ?? data['ErrorCode'];
    if (raw is int) return _fromValue(raw);
    if (raw is String) {
      final parsed = int.tryParse(raw);
      if (parsed != null) return _fromValue(parsed);
      return switch (raw) {
        'INVALID_PROFILE_PICTURE' => ErrorCodes.invalidProfilePicture,
        'PROFILE_PICTURE_TOO_LARGE' => ErrorCodes.profilePictureTooLarge,
        _ => ErrorCodes.unknownError,
      };
    }
    return ErrorCodes.unknownError;
  }

  ErrorCodes _fromValue(int value) {
    for (final item in ErrorCodes.values) {
      if (item.value == value) return item;
    }
    return ErrorCodes.unknownError;
  }
}
