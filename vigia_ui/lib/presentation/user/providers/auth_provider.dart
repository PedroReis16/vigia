import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/push_notification_provider.dart';
import 'package:vigia_ui/core/providers/repository_providers/auth_repository_provider.dart';
import 'package:vigia_ui/domain/DTOs/user_credentials.dart';
import 'package:vigia_ui/presentation/devices/providers/devices_provider.dart';
import 'package:vigia_ui/presentation/notifications/providers/notifications_provider.dart';
import 'package:vigia_ui/presentation/settings/providers/user_profile_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';

part 'auth_provider.g.dart';

class AuthState {
  const AuthState();
}

@riverpod
class AuthController extends _$AuthController {
  @override
  AuthState build() => const AuthState();

  /// Exchanges the Keycloak authorization code without opening the session,
  /// so the UI can close the sheet and arm the shell morph first.
  Future<UserCredentials?> completeLogin({
    required String code,
    required String codeVerifier,
  }) async {
    try {
      return await ref
          .read(authRepositoryProvider)
          .exchangeAuthorizationCode(code: code, codeVerifier: codeVerifier);
    } catch (_) {
      return null;
    }
  }

  Future<void> commitSession(UserCredentials credentials) async {
    // The shell replaces AuthPage as soon as the session flips, and this
    // provider is auto-dispose. Keep it alive until the reloads finish.
    final link = ref.keepAlive();
    try {
      await ref
          .read(authSessionProvider.notifier)
          .setAuthenticated(
            accessToken: credentials.accessToken,
            refreshToken: credentials.refreshToken,
          );
      if (!ref.mounted) return;
      ref.invalidate(userProfileProvider);
      await ref.read(devicesProvider.notifier).refresh(withDelay: false);
      if (!ref.mounted) return;
      await ref.read(pushNotificationCoordinatorProvider).syncAfterLogin();
      if (!ref.mounted) return;
      await ref.read(notificationsInboxProvider.notifier).refresh();
    } finally {
      link.close();
    }
  }
}
