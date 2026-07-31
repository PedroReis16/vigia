// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'auth_exit_transition_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning
/// Controls whether the Auth ↔ Shell navigation plays the morph transition.
///
/// [AuthTransitionKind.login] / [AuthTransitionKind.register] — shell enters
///   with veil + logo flight from the auth-form top position.
/// [AuthTransitionKind.coldStart] — shell enters with veil + logo flight from
///   screen center (no Flutter Hero — placeholders flash on devices).
/// [AuthTransitionKind.logout] — shell exits: AppBar expands to full-screen.
/// [AuthTransitionKind.none] — no enter morph armed yet.

@ProviderFor(AuthExitTransition)
final authExitTransitionProvider = AuthExitTransitionProvider._();

/// Controls whether the Auth ↔ Shell navigation plays the morph transition.
///
/// [AuthTransitionKind.login] / [AuthTransitionKind.register] — shell enters
///   with veil + logo flight from the auth-form top position.
/// [AuthTransitionKind.coldStart] — shell enters with veil + logo flight from
///   screen center (no Flutter Hero — placeholders flash on devices).
/// [AuthTransitionKind.logout] — shell exits: AppBar expands to full-screen.
/// [AuthTransitionKind.none] — no enter morph armed yet.
final class AuthExitTransitionProvider
    extends $NotifierProvider<AuthExitTransition, AuthTransitionKind> {
  /// Controls whether the Auth ↔ Shell navigation plays the morph transition.
  ///
  /// [AuthTransitionKind.login] / [AuthTransitionKind.register] — shell enters
  ///   with veil + logo flight from the auth-form top position.
  /// [AuthTransitionKind.coldStart] — shell enters with veil + logo flight from
  ///   screen center (no Flutter Hero — placeholders flash on devices).
  /// [AuthTransitionKind.logout] — shell exits: AppBar expands to full-screen.
  /// [AuthTransitionKind.none] — no enter morph armed yet.
  AuthExitTransitionProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'authExitTransitionProvider',
        isAutoDispose: false,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$authExitTransitionHash();

  @$internal
  @override
  AuthExitTransition create() => AuthExitTransition();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(AuthTransitionKind value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<AuthTransitionKind>(value),
    );
  }
}

String _$authExitTransitionHash() =>
    r'be3066f69393ca8a961590030adf249044694ddc';

/// Controls whether the Auth ↔ Shell navigation plays the morph transition.
///
/// [AuthTransitionKind.login] / [AuthTransitionKind.register] — shell enters
///   with veil + logo flight from the auth-form top position.
/// [AuthTransitionKind.coldStart] — shell enters with veil + logo flight from
///   screen center (no Flutter Hero — placeholders flash on devices).
/// [AuthTransitionKind.logout] — shell exits: AppBar expands to full-screen.
/// [AuthTransitionKind.none] — no enter morph armed yet.

abstract class _$AuthExitTransition extends $Notifier<AuthTransitionKind> {
  AuthTransitionKind build();
  @$mustCallSuper
  @override
  WhenComplete runBuild() {
    final ref = this.ref as $Ref<AuthTransitionKind, AuthTransitionKind>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<AuthTransitionKind, AuthTransitionKind>,
              AuthTransitionKind,
              Object?,
              Object?
            >;
    return element.handleCreate(ref, build);
  }
}
