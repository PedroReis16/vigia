import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/push_notification_provider.dart';
import 'package:vigia_ui/core/providers/repository_providers/auth_repository_provider.dart';
import 'package:vigia_ui/domain/DTOs/user_credentials.dart';
import 'package:vigia_ui/domain/enums/auth_status.dart';
import 'package:vigia_ui/domain/enums/error_codes.dart';
import 'package:vigia_ui/domain/exceptions/request_exception.dart';
import 'package:vigia_ui/domain/exceptions/unauthroized_exception.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';

part 'auth_provider.g.dart';

class AuthState {
  final bool isLoading;
  final String? error;
  final AuthStatus? status;
  final ErrorCodes? errorCode;

  AuthState({this.isLoading = false, this.error, this.status, this.errorCode});
}

@riverpod
class AuthController extends _$AuthController {
  @override
  AuthState build() => AuthState();

  /// Authenticates and returns credentials without opening the session,
  /// so the UI can show a welcome beat before navigating to the shell.
  Future<UserCredentials?> login(String email, String password) async {
    state = AuthState(isLoading: true);

    try {
      final credentials = await ref
          .read(authRepositoryProvider)
          .login(email, password);

      state = AuthState(isLoading: false, status: AuthStatus.authorized);
      return credentials;
    } on UnauthorizedException {
      state = AuthState(isLoading: false, status: AuthStatus.unauthorized);
      return null;
    } catch (e) {
      state = AuthState(isLoading: false, status: AuthStatus.error);
      return null;
    }
  }

  /// Creates the account and returns credentials without opening the session,
  /// so the UI can show a welcome beat before navigating to the shell.
  Future<UserCredentials?> register(
    String name,
    String email,
    String password,
  ) async {
    state = AuthState(isLoading: true);

    try {
      final credentials = await ref
          .read(authRepositoryProvider)
          .register(name, email, password);

      state = AuthState(isLoading: false, status: AuthStatus.authorized);
      return credentials;
    } on UnauthorizedException {
      state = AuthState(isLoading: false, status: AuthStatus.unauthorized);
      return null;
    } on RequestException catch (e) {
      state = AuthState(
        isLoading: false,
        status: AuthStatus.error,
        errorCode: e.errorCode,
      );
      return null;
    } catch (e) {
      state = AuthState(isLoading: false, status: AuthStatus.error);
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
