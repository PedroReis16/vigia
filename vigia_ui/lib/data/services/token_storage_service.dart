import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:jwt_decoder/jwt_decoder.dart';

class TokenStorageService {
  static const String _accessTokenKey = 'access_token';
  static const String _refreshTokenKey = 'refresh_token';
  static const String _userIdKey = 'user_id';

  final _storage = FlutterSecureStorage();

  Future<void> saveUserTokens(String accessToken, String refreshToken) async {
    Map<String, dynamic> decodedToken = JwtDecoder.decode(accessToken);

    final String userId = decodedToken['sub'] as String;

    await _storage.write(key: _userIdKey, value: userId);

    await _storage.write(key: _accessTokenKey, value: accessToken);
    await _storage.write(key: _refreshTokenKey, value: refreshToken);
  }

  Future<void> clearUserTokens() async {
    await _storage.delete(key: _accessTokenKey);
    await _storage.delete(key: _refreshTokenKey);
  }

  Future<String?> getAccessToken() async {
    return await _storage.read(key: _accessTokenKey);
  }

  Future<String?> getRefreshToken() async {
    return await _storage.read(key: _refreshTokenKey);
  }

  Future<String> getUserId() async {
    final String? userId = await _storage.read(key: _userIdKey);
    if (userId == null) {
      throw Exception('User ID not found');
    }
    return userId;
  }
}
