import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'auth_exit_transition_provider.g.dart';

enum AuthTransitionKind { none, login, register, logout, coldStart }

/// Controls whether the Auth ↔ Shell navigation plays the morph transition.
///
/// [AuthTransitionKind.login] / [AuthTransitionKind.register] — shell enters
///   with veil + logo flight from the auth-form top position.
/// [AuthTransitionKind.coldStart] — shell enters with veil + logo flight from
///   screen center (no Flutter Hero — placeholders flash on devices).
/// [AuthTransitionKind.logout] — shell exits: AppBar expands to full-screen.
/// [AuthTransitionKind.none] — no enter morph armed yet.
@Riverpod(keepAlive: true)
class AuthExitTransition extends _$AuthExitTransition {
  @override
  AuthTransitionKind build() => AuthTransitionKind.none;

  void armLogin() => state = AuthTransitionKind.login;

  void armRegister() => state = AuthTransitionKind.register;

  void armColdStart() => state = AuthTransitionKind.coldStart;

  void armLogout() => state = AuthTransitionKind.logout;

  void disarm() => state = AuthTransitionKind.none;
}
