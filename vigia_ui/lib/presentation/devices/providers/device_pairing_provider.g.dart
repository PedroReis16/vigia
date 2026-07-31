// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'device_pairing_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(DevicePairing)
final devicePairingProvider = DevicePairingProvider._();

final class DevicePairingProvider
    extends $NotifierProvider<DevicePairing, DevicePairingState> {
  DevicePairingProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'devicePairingProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$devicePairingHash();

  @$internal
  @override
  DevicePairing create() => DevicePairing();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(DevicePairingState value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<DevicePairingState>(value),
    );
  }
}

String _$devicePairingHash() => r'b12c542b9d2eb00d4875d3464ff1d8538672a16e';

abstract class _$DevicePairing extends $Notifier<DevicePairingState> {
  DevicePairingState build();
  @$mustCallSuper
  @override
  WhenComplete runBuild() {
    final ref = this.ref as $Ref<DevicePairingState, DevicePairingState>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<DevicePairingState, DevicePairingState>,
              DevicePairingState,
              Object?,
              Object?
            >;
    return element.handleCreate(ref, build);
  }
}
