// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'devices_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(getDevices)
final getDevicesProvider = GetDevicesProvider._();

final class GetDevicesProvider
    extends
        $FunctionalProvider<
          AsyncValue<List<Device>>,
          List<Device>,
          FutureOr<List<Device>>
        >
    with $FutureModifier<List<Device>>, $FutureProvider<List<Device>> {
  GetDevicesProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'getDevicesProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$getDevicesHash();

  @$internal
  @override
  $FutureProviderElement<List<Device>> $createElement(
    $ProviderPointer pointer,
  ) => $FutureProviderElement(pointer);

  @override
  FutureOr<List<Device>> create(Ref ref) {
    return getDevices(ref);
  }
}

String _$getDevicesHash() => r'8bd2b044797cc70d531456f0e57d107894dfa9bd';

@ProviderFor(Devices)
final devicesProvider = DevicesProvider._();

final class DevicesProvider
    extends $AsyncNotifierProvider<Devices, List<Device>> {
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

String _$devicesHash() => r'dc832da4e74280beec62e66fa6ef57f25cd6efa8';

abstract class _$Devices extends $AsyncNotifier<List<Device>> {
  FutureOr<List<Device>> build();
  @$mustCallSuper
  @override
  WhenComplete runBuild() {
    final ref = this.ref as $Ref<AsyncValue<List<Device>>, List<Device>>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<AsyncValue<List<Device>>, List<Device>>,
              AsyncValue<List<Device>>,
              Object?,
              Object?
            >;
    return element.handleCreate(ref, build);
  }
}
