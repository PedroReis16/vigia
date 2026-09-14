import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/repository_providers/devices_repository_provider.dart';
import 'package:vigia_ui/domain/environments.dart';

part 'device_live_provider.g.dart';

String deviceStreamUrl(String deviceId) =>
    '${Environments.streamBaseUrl}/live/$deviceId';

String deviceWhepUrl(String deviceId) => '${deviceStreamUrl(deviceId)}/whep';

@riverpod
Future<void> startDeviceStreaming(Ref ref, String deviceId) async {
  await ref
      .read(devicesRepositoryProvider)
      .sendCommand(deviceId, 'START_STREAMING');
}
