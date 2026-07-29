import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/repository_providers/auth_repository.dart';
import 'package:vigia_ui/domain/enums/auth_status.dart';
import 'package:vigia_ui/domain/exceptions/unauthroized_exception.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';

part 'auth_provider.g.dart';

class AuthState {
  final bool isLoading;
  final String? error;
  final AuthStatus? status;

  AuthState({this.isLoading = false, this.error, this.status});
}

@riverpod
class AuthController extends _$AuthController {
  @override
  AuthState build() => AuthState();

  Future<void> login(String email, String password) async {
    state = AuthState(isLoading: true);

    try {
      final credentials = await ref
          .read(authRepositoryProvider)
          .login(email, password);

      await ref
          .read(authSessionProvider.notifier)
          .setAuthenticated(
            accessToken: credentials.accessToken,
            refreshToken: credentials.refreshToken,
          );

      state = AuthState(isLoading: false, status: AuthStatus.authorized);
    } on UnauthorizedException {
      state = AuthState(isLoading: false, status: AuthStatus.unauthorized);
    } catch (e) {
      state = AuthState(isLoading: false, status: AuthStatus.error);
    }
  }
}
