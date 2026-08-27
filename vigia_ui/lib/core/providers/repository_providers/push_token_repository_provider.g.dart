// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'push_token_repository_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(pushTokenRepository)
final pushTokenRepositoryProvider = PushTokenRepositoryProvider._();

final class PushTokenRepositoryProvider
    extends
        $FunctionalProvider<
          PushTokenRepository,
          PushTokenRepository,
          PushTokenRepository
        >
    with $Provider<PushTokenRepository> {
  PushTokenRepositoryProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'pushTokenRepositoryProvider',
        isAutoDispose: false,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$pushTokenRepositoryHash();

  @$internal
  @override
  $ProviderElement<PushTokenRepository> $createElement(
    $ProviderPointer pointer,
  ) => $ProviderElement(pointer);

  @override
  PushTokenRepository create(Ref ref) {
    return pushTokenRepository(ref);
  }

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(PushTokenRepository value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<PushTokenRepository>(value),
    );
  }
}

String _$pushTokenRepositoryHash() =>
    r'806c339a27a68542493a021443b25caf34ad794c';
