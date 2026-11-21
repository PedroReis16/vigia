import 'dart:async';

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
  /// The in-memory flag flips even if secure storage is slow or unavailable.
  Future<void> clearSession() async {
    try {
      await ref
          .read(tokenStorageProvider)
          .clearUserTokens()
          .timeout(const Duration(seconds: 2));
    } catch (_) {}
    state = const AsyncData(false);
  }

  /// Ends the session locally immediately, then best-effort revokes on the API.
  ///
  /// Returns as soon as the local session is cleared so the router can leave the
  /// shell even when Keycloak, secure storage, cookies, or the network stall.
  /// Remote logout uses a snapshot Bearer after storage is wiped and is not awaited.
  Future<void> signOut() async {
    final tokenStorage = ref.read(tokenStorageProvider);
    final authRepository = ref.read(authRepositoryProvider);

    String? accessToken;
    String? refreshToken;
    try {
      accessToken = await tokenStorage
          .getAccessToken()
          .timeout(const Duration(seconds: 2));
      refreshToken = await tokenStorage
          .getRefreshToken()
          .timeout(const Duration(seconds: 2));
    } catch (_) {}

    final pushCoordinator = ref.read(pushNotificationCoordinatorProvider);
    final pushToken = pushCoordinator.currentPushToken;

    // Redirect depends on this — never block it on the network or WebView cookies.
    pushCoordinator.clearLocalToken();
    state = const AsyncData(false);
    try {
      await tokenStorage.clearUserTokens().timeout(const Duration(seconds: 2));
    } catch (_) {}

    unawaited(() async {
      if (refreshToken != null && refreshToken.isNotEmpty) {
        try {
          await authRepository
              .logout(
                refreshToken: refreshToken,
                pushToken: pushToken,
                accessToken: accessToken,
              )
              .timeout(const Duration(seconds: 5));
        } catch (_) {}
      }

      try {
        await ref
            .read(keycloakBrowserSessionProvider)
            .clear()
            .timeout(const Duration(seconds: 2));
      } catch (_) {}
    }());
  }
}
