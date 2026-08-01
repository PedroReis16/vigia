// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'devices_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(Devices)
final devicesProvider = DevicesProvider._();

final class DevicesProvider
    extends $AsyncNotifierProvider<Devices, List<DeviceUIModel>> {
  DevicesProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'devicesProvider',
        isAutoDispose: false,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$devicesHash();

  @$internal
  @override
  Devices create() => Devices();
}

String _$devicesHash() => r'1f7760ec3a278bcb373a7e08ab74d102c9ab9890';

abstract class _$Devices extends $AsyncNotifier<List<DeviceUIModel>> {
  FutureOr<List<DeviceUIModel>> build();
  @$mustCallSuper
  @override
  WhenComplete runBuild() {
    final ref =
        this.ref as $Ref<AsyncValue<List<DeviceUIModel>>, List<DeviceUIModel>>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<AsyncValue<List<DeviceUIModel>>, List<DeviceUIModel>>,
              AsyncValue<List<DeviceUIModel>>,
              Object?,
              Object?
            >;
    return element.handleCreate(ref, build);
  }
}

@ProviderFor(addDevice)
final addDeviceProvider = AddDeviceFamily._();

final class AddDeviceProvider extends $FunctionalProvider<void, void, void>
    with $Provider<void> {
  AddDeviceProvider._({
    required AddDeviceFamily super.from,
    required NewDevice super.argument,
  }) : super(
         retry: null,
         name: r'addDeviceProvider',
         isAutoDispose: true,
         dependencies: null,
         $allTransitiveDependencies: null,
       );

  @override
  String debugGetCreateSourceHash() => _$addDeviceHash();

  @override
  String toString() {
    return r'addDeviceProvider'
        ''
        '($argument)';
  }

  @$internal
  @override
  $ProviderElement<void> $createElement($ProviderPointer pointer) =>
      $ProviderElement(pointer);

  @override
  void create(Ref ref) {
    final argument = this.argument as NewDevice;
    return addDevice(ref, argument);
  }

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(void value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<void>(value),
    );
  }

  @override
  bool operator ==(Object other) {
    return other is AddDeviceProvider && other.argument == argument;
  }

  @override
  int get hashCode {
    return argument.hashCode;
  }
}

String _$addDeviceHash() => r'702c991bad9fa8962176ef9276934ab8ab03f5e7';

final class AddDeviceFamily extends $Family
    with $FunctionalFamilyOverride<void, NewDevice> {
  AddDeviceFamily._()
    : super(
        retry: null,
        name: r'addDeviceProvider',
        dependencies: null,
        $allTransitiveDependencies: null,
        isAutoDispose: true,
      );

  AddDeviceProvider call(NewDevice newDevice) =>
      AddDeviceProvider._(argument: newDevice, from: this);

  @override
  String toString() => r'addDeviceProvider';
}
