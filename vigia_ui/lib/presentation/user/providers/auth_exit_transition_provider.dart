import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'auth_exit_transition_provider.g.dart';

enum AuthTransitionKind { none, login, register, logout }

/// Controls whether the Auth ↔ Shell navigation plays the morph transition.
///
/// [AuthTransitionKind.login]  — shell enters: primary veil shrinks to AppBar.
/// [AuthTransitionKind.register] — shell enters: primary veil shrinks to AppBar.
/// [AuthTransitionKind.logout] — shell exits: AppBar expands to full-screen.
/// [AuthTransitionKind.none]   — cold start / silent redirect, no animation.
@Riverpod(keepAlive: true)
class AuthExitTransition extends _$AuthExitTransition {
  @override
  AuthTransitionKind build() => AuthTransitionKind.none;

  void armLogin() => state = AuthTransitionKind.login;

  void armRegister() => state = AuthTransitionKind.register;

  void armLogout() => state = AuthTransitionKind.logout;

  void disarm() => state = AuthTransitionKind.none;
}
