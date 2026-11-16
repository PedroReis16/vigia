// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'device_clips_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(DeviceClipsList)
final deviceClipsListProvider = DeviceClipsListFamily._();

final class DeviceClipsListProvider
    extends $AsyncNotifierProvider<DeviceClipsList, List<DeviceClipUi>> {
  DeviceClipsListProvider._({
    required DeviceClipsListFamily super.from,
    required String super.argument,
  }) : super(
         retry: null,
         name: r'deviceClipsListProvider',
         isAutoDispose: true,
         dependencies: null,
         $allTransitiveDependencies: null,
       );

  @override
  String debugGetCreateSourceHash() => _$deviceClipsListHash();

  @override
  String toString() {
    return r'deviceClipsListProvider'
        ''
        '($argument)';
  }

  @$internal
  @override
  DeviceClipsList create() => DeviceClipsList();

  @override
  bool operator ==(Object other) {
    return other is DeviceClipsListProvider && other.argument == argument;
  }

  @override
  int get hashCode {
    return argument.hashCode;
  }
}

String _$deviceClipsListHash() => r'8c1e0a4b7d2f49e6a3c5b8d1e7f04a92c6b3d5e8';

final class DeviceClipsListFamily extends $Family
    with
        $ClassFamilyOverride<
          DeviceClipsList,
          AsyncValue<List<DeviceClipUi>>,
          List<DeviceClipUi>,
          FutureOr<List<DeviceClipUi>>,
          String
        > {
  DeviceClipsListFamily._()
    : super(
        retry: null,
        name: r'deviceClipsListProvider',
        dependencies: null,
        $allTransitiveDependencies: null,
        isAutoDispose: true,
      );

  DeviceClipsListProvider call(String deviceId) =>
      DeviceClipsListProvider._(argument: deviceId, from: this);

  @override
  String toString() => r'deviceClipsListProvider';
}

abstract class _$DeviceClipsList extends $AsyncNotifier<List<DeviceClipUi>> {
  late final _$args = ref.$arg as String;
  String get deviceId => _$args;

  FutureOr<List<DeviceClipUi>> build(String deviceId);
  @$mustCallSuper
  @override
  WhenComplete runBuild() {
    final ref =
        this.ref as $Ref<AsyncValue<List<DeviceClipUi>>, List<DeviceClipUi>>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<AsyncValue<List<DeviceClipUi>>, List<DeviceClipUi>>,
              AsyncValue<List<DeviceClipUi>>,
              Object?,
              Object?
            >;
    return element.handleCreate(ref, () => build(_$args));
  }
}
