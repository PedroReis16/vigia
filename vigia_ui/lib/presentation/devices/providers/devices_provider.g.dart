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

String _$devicesHash() => r'a1e3f91659ab39928a2d224991bf940f3e7e0d81';

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
