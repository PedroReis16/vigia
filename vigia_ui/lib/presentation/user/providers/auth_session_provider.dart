import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/push_notification_provider.dart';
import 'package:vigia_ui/core/providers/repository_providers/auth_repository_provider.dart';
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

  /// Clears local tokens and marks the session as signed out.
  /// Safe to call from Dio interceptors (does not hit the network).
  Future<void> clearSession() async {
    await ref.read(tokenStorageProvider).clearUserTokens();
    state = const AsyncData(false);
  }

  Future<void> signOut() async {
    final tokenStorage = ref.read(tokenStorageProvider);
    final authRepository = ref.read(authRepositoryProvider);
    final refreshToken = await tokenStorage.getRefreshToken();

    // Remove push token while the access token is still available.
    try {
      await ref.read(pushNotificationCoordinatorProvider).unregisterCurrentToken();
    } catch (_) {}

    // Clear locally first so GoRouter redirect runs immediately.
    await clearSession();

    // Best-effort server revoke; failures must not block/undo local logout.
    if (refreshToken != null) {
      try {
        await authRepository.logout(refreshToken);
      } catch (_) {}
    }
  }
}
