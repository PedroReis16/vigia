// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'auth_exit_transition_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning
/// Controls whether the Auth ↔ Shell navigation plays the morph transition.
///
/// [AuthTransitionKind.login]  — shell enters: primary veil shrinks to AppBar.
/// [AuthTransitionKind.register] — shell enters: primary veil shrinks to AppBar.
/// [AuthTransitionKind.logout] — shell exits: AppBar expands to full-screen.
/// [AuthTransitionKind.none]   — cold start / silent redirect, no animation.

@ProviderFor(AuthExitTransition)
final authExitTransitionProvider = AuthExitTransitionProvider._();

/// Controls whether the Auth ↔ Shell navigation plays the morph transition.
///
/// [AuthTransitionKind.login]  — shell enters: primary veil shrinks to AppBar.
/// [AuthTransitionKind.register] — shell enters: primary veil shrinks to AppBar.
/// [AuthTransitionKind.logout] — shell exits: AppBar expands to full-screen.
/// [AuthTransitionKind.none]   — cold start / silent redirect, no animation.
final class AuthExitTransitionProvider
    extends $NotifierProvider<AuthExitTransition, AuthTransitionKind> {
  /// Controls whether the Auth ↔ Shell navigation plays the morph transition.
  ///
  /// [AuthTransitionKind.login]  — shell enters: primary veil shrinks to AppBar.
  /// [AuthTransitionKind.register] — shell enters: primary veil shrinks to AppBar.
  /// [AuthTransitionKind.logout] — shell exits: AppBar expands to full-screen.
  /// [AuthTransitionKind.none]   — cold start / silent redirect, no animation.
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
    r'6fc5e67bb5ce8821ecdb0139ff75534d407c5be9';

/// Controls whether the Auth ↔ Shell navigation plays the morph transition.
///
/// [AuthTransitionKind.login]  — shell enters: primary veil shrinks to AppBar.
/// [AuthTransitionKind.register] — shell enters: primary veil shrinks to AppBar.
/// [AuthTransitionKind.logout] — shell exits: AppBar expands to full-screen.
/// [AuthTransitionKind.none]   — cold start / silent redirect, no animation.

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
