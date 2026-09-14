import 'package:vigia_ui/data/services/token_storage_service.dart';

/// In-memory [TokenStorageService] for tests (no secure-storage / JWT).
class FakeTokenStorage extends TokenStorageService {
  FakeTokenStorage({this.accessToken, this.refreshToken, this.userId});

  String? accessToken;
  String? refreshToken;
  String? userId;

  @override
  Future<void> saveUserTokens(String access, String refresh) async {
    accessToken = access;
    refreshToken = refresh;
    userId ??= 'test-user';
  }

  @override
  Future<void> clearUserTokens() async {
    accessToken = null;
    refreshToken = null;
  }

  @override
  Future<String?> getAccessToken() async => accessToken;

  @override
  Future<String?> getRefreshToken() async => refreshToken;

  @override
  Future<String> getUserId() async {
    final id = userId;
    if (id == null) {
      throw Exception('User ID not found');
    }
    return id;
  }
}
