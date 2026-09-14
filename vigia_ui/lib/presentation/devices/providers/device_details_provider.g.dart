// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'device_details_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(getDeviceUsers)
final getDeviceUsersProvider = GetDeviceUsersFamily._();

final class GetDeviceUsersProvider
    extends
        $FunctionalProvider<
          AsyncValue<List<UserUIModel>>,
          List<UserUIModel>,
          FutureOr<List<UserUIModel>>
        >
    with
        $FutureModifier<List<UserUIModel>>,
        $FutureProvider<List<UserUIModel>> {
  GetDeviceUsersProvider._({
    required GetDeviceUsersFamily super.from,
    required String super.argument,
  }) : super(
         retry: null,
         name: r'getDeviceUsersProvider',
         isAutoDispose: true,
         dependencies: null,
         $allTransitiveDependencies: null,
       );

  @override
  String debugGetCreateSourceHash() => _$getDeviceUsersHash();

  @override
  String toString() {
    return r'getDeviceUsersProvider'
        ''
        '($argument)';
  }

  @$internal
  @override
  $FutureProviderElement<List<UserUIModel>> $createElement(
    $ProviderPointer pointer,
  ) => $FutureProviderElement(pointer);

  @override
  FutureOr<List<UserUIModel>> create(Ref ref) {
    final argument = this.argument as String;
    return getDeviceUsers(ref, argument);
  }

  @override
  bool operator ==(Object other) {
    return other is GetDeviceUsersProvider && other.argument == argument;
  }

  @override
  int get hashCode {
    return argument.hashCode;
  }
}

String _$getDeviceUsersHash() => r'88e0f752020aebe578fb2ae7589baedb6f37b93d';

final class GetDeviceUsersFamily extends $Family
    with $FunctionalFamilyOverride<FutureOr<List<UserUIModel>>, String> {
  GetDeviceUsersFamily._()
    : super(
        retry: null,
        name: r'getDeviceUsersProvider',
        dependencies: null,
        $allTransitiveDependencies: null,
        isAutoDispose: true,
      );

  GetDeviceUsersProvider call(String deviceId) =>
      GetDeviceUsersProvider._(argument: deviceId, from: this);

  @override
  String toString() => r'getDeviceUsersProvider';
}

@ProviderFor(DeviceShareActions)
final deviceShareActionsProvider = DeviceShareActionsProvider._();

final class DeviceShareActionsProvider
    extends $NotifierProvider<DeviceShareActions, AsyncValue<void>> {
  DeviceShareActionsProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'deviceShareActionsProvider',
        isAutoDispose: false,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$deviceShareActionsHash();

  @$internal
  @override
  DeviceShareActions create() => DeviceShareActions();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(AsyncValue<void> value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<AsyncValue<void>>(value),
    );
  }
}

String _$deviceShareActionsHash() =>
    r'ecf7f2d7ae804bd2a7bf5c242f33ec23e61cc02f';

abstract class _$DeviceShareActions extends $Notifier<AsyncValue<void>> {
  AsyncValue<void> build();
  @$mustCallSuper
  @override
  WhenComplete runBuild() {
    final ref = this.ref as $Ref<AsyncValue<void>, AsyncValue<void>>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<AsyncValue<void>, AsyncValue<void>>,
              AsyncValue<void>,
              Object?,
              Object?
            >;
    return element.handleCreate(ref, build);
  }
}
