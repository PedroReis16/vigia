// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'push_notification_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(pushNotificationCoordinator)
final pushNotificationCoordinatorProvider =
    PushNotificationCoordinatorProvider._();

final class PushNotificationCoordinatorProvider
    extends
        $FunctionalProvider<
          PushNotificationCoordinator,
          PushNotificationCoordinator,
          PushNotificationCoordinator
        >
    with $Provider<PushNotificationCoordinator> {
  PushNotificationCoordinatorProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'pushNotificationCoordinatorProvider',
        isAutoDispose: false,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$pushNotificationCoordinatorHash();

  @$internal
  @override
  $ProviderElement<PushNotificationCoordinator> $createElement(
    $ProviderPointer pointer,
  ) => $ProviderElement(pointer);

  @override
  PushNotificationCoordinator create(Ref ref) {
    return pushNotificationCoordinator(ref);
  }

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(PushNotificationCoordinator value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<PushNotificationCoordinator>(value),
    );
  }
}

String _$pushNotificationCoordinatorHash() =>
    r'59d19ff6671ce431b648358d3b0062a2c754a892';
