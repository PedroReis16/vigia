// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'device_groups_realtime_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(deviceGroupsRealtimeService)
final deviceGroupsRealtimeServiceProvider =
    DeviceGroupsRealtimeServiceProvider._();

final class DeviceGroupsRealtimeServiceProvider
    extends
        $FunctionalProvider<
          DeviceGroupsRealtimeService,
          DeviceGroupsRealtimeService,
          DeviceGroupsRealtimeService
        >
    with $Provider<DeviceGroupsRealtimeService> {
  DeviceGroupsRealtimeServiceProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'deviceGroupsRealtimeServiceProvider',
        isAutoDispose: false,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$deviceGroupsRealtimeServiceHash();

  @$internal
  @override
  $ProviderElement<DeviceGroupsRealtimeService> $createElement(
    $ProviderPointer pointer,
  ) => $ProviderElement(pointer);

  @override
  DeviceGroupsRealtimeService create(Ref ref) {
    return deviceGroupsRealtimeService(ref);
  }

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(DeviceGroupsRealtimeService value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<DeviceGroupsRealtimeService>(value),
    );
  }
}

String _$deviceGroupsRealtimeServiceHash() =>
    r'65c64bf4f55b51954f82c624747ae0fbaa2f0fd3';

/// Keeps the SignalR connection alive while the user is authenticated and
/// refreshes device/user lists when group membership changes.

@ProviderFor(DeviceGroupsRealtimeBridge)
final deviceGroupsRealtimeBridgeProvider =
    DeviceGroupsRealtimeBridgeProvider._();

/// Keeps the SignalR connection alive while the user is authenticated and
/// refreshes device/user lists when group membership changes.
final class DeviceGroupsRealtimeBridgeProvider
    extends $NotifierProvider<DeviceGroupsRealtimeBridge, void> {
  /// Keeps the SignalR connection alive while the user is authenticated and
  /// refreshes device/user lists when group membership changes.
  DeviceGroupsRealtimeBridgeProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'deviceGroupsRealtimeBridgeProvider',
        isAutoDispose: false,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$deviceGroupsRealtimeBridgeHash();

  @$internal
  @override
  DeviceGroupsRealtimeBridge create() => DeviceGroupsRealtimeBridge();

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(void value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<void>(value),
    );
  }
}

String _$deviceGroupsRealtimeBridgeHash() =>
    r'496653f96f690f5da86230fd8f2a487c4c9fcf4a';

/// Keeps the SignalR connection alive while the user is authenticated and
/// refreshes device/user lists when group membership changes.

abstract class _$DeviceGroupsRealtimeBridge extends $Notifier<void> {
  void build();
  @$mustCallSuper
  @override
  WhenComplete runBuild() {
    final ref = this.ref as $Ref<void, void>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<void, void>,
              void,
              Object?,
              Object?
            >;
    return element.handleCreate(ref, build);
  }
}
