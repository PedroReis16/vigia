import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/token_storage_provider.dart';

part 'auth_session_provider.g.dart';

/// Whether the user has a persisted session (refresh token present).
@Riverpod(keepAlive: true)
class AuthSession extends _$AuthSession {
  @override
  Future<bool> build() async {
    final refreshToken = await ref.read(tokenStorageProvider).getRefreshToken();
    return refreshToken != null && refreshToken.isNotEmpty;
  }

  Future<void> setAuthenticated({
    required String accessToken,
    required String refreshToken,
  }) async {
    await ref
        .read(tokenStorageProvider)
        .saveUserTokens(accessToken, refreshToken);
    state = const AsyncData(true);
  }

  Future<void> signOut() async {
    await ref.read(tokenStorageProvider).clearUserTokens();
    state = const AsyncData(false);
  }
}
