import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/repository_providers/devices_repository_provider.dart';
import 'package:vigia_ui/domain/DTOs/device.dart';
import 'package:vigia_ui/domain/enums/error_codes.dart';

part 'devices_provider.g.dart';

class DevicesState {
  final String? errorMessage;
  final ErrorCodes? errorCode;
  final List<Device> devices;

  DevicesState({this.errorMessage, this.errorCode, this.devices = const []});
}

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
    state = await AsyncValue.guard(() async => await _loadDevices());
  }

  Future<List<Device>> _loadDevices() async {
    try {
      await Future.delayed(
        const Duration(milliseconds: 1000),
      ); //Delay para esperar a animação de transição se concluída antes de realizar o carregamento dos dispositivos

      final devices = await ref.read(devicesRepositoryProvider).getDevices();
      return devices;
    } catch (e) {
      rethrow;
    }
  }

  void addDevice(Device device) {
    final current = state.asData?.value ?? [];
    state = AsyncData([device, ...current]);
  }
}
