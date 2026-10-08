import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/push_notification_provider.dart';
import 'package:vigia_ui/core/providers/repository_providers/auth_repository_provider.dart';
import 'package:vigia_ui/domain/DTOs/user_credentials.dart';
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
    await ref
        .read(authSessionProvider.notifier)
        .setAuthenticated(
          accessToken: credentials.accessToken,
          refreshToken: credentials.refreshToken,
        );
    await ref.read(pushNotificationCoordinatorProvider).syncAfterLogin();
  }
}
