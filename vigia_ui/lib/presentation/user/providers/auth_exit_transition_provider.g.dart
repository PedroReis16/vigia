// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'auth_exit_transition_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(AuthExitTransition)
final authExitTransitionProvider = AuthExitTransitionProvider._();

final class AuthExitTransitionProvider
    extends $NotifierProvider<AuthExitTransition, AuthTransitionKind> {
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

String _$authExitTransitionHash() => r'auth_exit_transition_manual';

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
