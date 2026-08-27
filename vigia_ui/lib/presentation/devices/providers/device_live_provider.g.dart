// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'device_live_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(startDeviceStreaming)
final startDeviceStreamingProvider = StartDeviceStreamingFamily._();

final class StartDeviceStreamingProvider
    extends $FunctionalProvider<AsyncValue<void>, void, FutureOr<void>>
    with $FutureModifier<void>, $FutureProvider<void> {
  StartDeviceStreamingProvider._({
    required StartDeviceStreamingFamily super.from,
    required String super.argument,
  }) : super(
         retry: null,
         name: r'startDeviceStreamingProvider',
         isAutoDispose: true,
         dependencies: null,
         $allTransitiveDependencies: null,
       );

  @override
  String debugGetCreateSourceHash() => _$startDeviceStreamingHash();

  @override
  String toString() {
    return r'startDeviceStreamingProvider'
        ''
        '($argument)';
  }

  @$internal
  @override
  $FutureProviderElement<void> $createElement($ProviderPointer pointer) =>
      $FutureProviderElement(pointer);

  @override
  FutureOr<void> create(Ref ref) {
    final argument = this.argument as String;
    return startDeviceStreaming(ref, argument);
  }

  @override
  bool operator ==(Object other) {
    return other is StartDeviceStreamingProvider && other.argument == argument;
  }

  @override
  int get hashCode {
    return argument.hashCode;
  }
}

String _$startDeviceStreamingHash() =>
    r'd8eedab0ad702e87c08df18920f31791849d1ea9';

final class StartDeviceStreamingFamily extends $Family
    with $FunctionalFamilyOverride<FutureOr<void>, String> {
  StartDeviceStreamingFamily._()
    : super(
        retry: null,
        name: r'startDeviceStreamingProvider',
        dependencies: null,
        $allTransitiveDependencies: null,
        isAutoDispose: true,
      );

  StartDeviceStreamingProvider call(String deviceId) =>
      StartDeviceStreamingProvider._(argument: deviceId, from: this);

  @override
  String toString() => r'startDeviceStreamingProvider';
}
