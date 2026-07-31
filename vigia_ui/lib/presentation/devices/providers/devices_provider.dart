import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:uuid/uuid.dart';
import 'package:vigia_ui/core/providers/repository_providers/devices_repository_provider.dart';
import 'package:vigia_ui/domain/DTOs/device.dart';
import 'package:vigia_ui/domain/enums/device_rooms.dart';

part 'devices_provider.g.dart';

@riverpod
Future<List<Device>> getDevices(Ref ref) async {
  try {
    await Future.delayed(const Duration(seconds: 10));

    return [];
  } catch (e) {
    throw Exception('Failed to load devices');
  }
}

@Riverpod(keepAlive: true)
class Devices extends _$Devices {
  @override
  Future<List<Device>> build() {
    return _loadDevices();
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_loadDevices);
  }

  Future<List<Device>> _loadDevices() async {
    try {
      final devices = await ref.read(devicesRepositoryProvider).getDevices();
      return devices;
    } catch (e) {
      throw Exception('Failed to load devices');
    }
  }

  void addDevice(Device device) {
    final current = state.asData?.value ?? [];
    state = AsyncData([device, ...current]);
  }
}
