// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'cold_start_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning
/// Whether the app cold-start intro has already run in this process.
///
/// `false` until AuthPage finishes the first boot sequence (intro to forms or
/// redirect to shell). Logout skips cold start because this stays `true`.

@ProviderFor(ColdStartCompleted)
final coldStartCompletedProvider = ColdStartCompletedProvider._();

/// Whether the app cold-start intro has already run in this process.
///
/// `false` until AuthPage finishes the first boot sequence (intro to forms or
/// redirect to shell). Logout skips cold start because this stays `true`.
final class ColdStartCompletedProvider
    extends $NotifierProvider<ColdStartCompleted, bool> {
  /// Whether the app cold-start intro has already run in this process.
  ///
  /// `false` until AuthPage finishes the first boot sequence (intro to forms or
  /// redirect to shell). Logout skips cold start because this stays `true`.
  ColdStartCompletedProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'coldStartCompletedProvider',
        isAutoDispose: false,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$coldStartCompletedHash();

  @$internal
  @override
  ColdStartCompleted create() => ColdStartCompleted();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(bool value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<bool>(value),
    );
  }
}

String _$coldStartCompletedHash() =>
    r'536d879c26d79b72d03e45faf7642d2ddf251fbd';

/// Whether the app cold-start intro has already run in this process.
///
/// `false` until AuthPage finishes the first boot sequence (intro to forms or
/// redirect to shell). Logout skips cold start because this stays `true`.

abstract class _$ColdStartCompleted extends $Notifier<bool> {
  bool build();
  @$mustCallSuper
  @override
  WhenComplete runBuild() {
    final ref = this.ref as $Ref<bool, bool>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<bool, bool>,
              bool,
              Object?,
              Object?
            >;
    return element.handleCreate(ref, build);
  }
}
