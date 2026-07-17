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

String _$getDevicesHash() => r'c5ad3bd85b55c4c6370d26e67caddc86b4d5b7f8';
