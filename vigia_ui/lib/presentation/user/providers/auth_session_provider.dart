import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/keycloak_auth_client_provider.dart';
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

  /// Ends the Keycloak session via the API; only clears local state on success.
  Future<void> signOut() async {
    final tokenStorage = ref.read(tokenStorageProvider);
    final authRepository = ref.read(authRepositoryProvider);
    final refreshToken = await tokenStorage.getRefreshToken();

    if (refreshToken == null || refreshToken.isEmpty) {
      await clearSession();
      return;
    }

    final pushCoordinator = ref.read(pushNotificationCoordinatorProvider);
    final pushToken = pushCoordinator.currentPushToken;

    // Access token must still be valid for Authorization on POST /users/logout.
    await authRepository.logout(
      refreshToken: refreshToken,
      pushToken: pushToken,
    );

    pushCoordinator.clearLocalToken();
    await clearSession();

    try {
      await ref.read(keycloakBrowserSessionProvider).clear();
    } catch (_) {}
  }
}
