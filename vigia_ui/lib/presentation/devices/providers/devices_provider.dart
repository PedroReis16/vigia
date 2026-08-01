import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/repository_providers/devices_repository_provider.dart';
import 'package:vigia_ui/data/services/token_storage_service.dart';
import 'package:vigia_ui/domain/DTOs/new_device.dart';
import 'package:vigia_ui/domain/enums/device_rooms.dart';
import 'package:vigia_ui/domain/enums/error_codes.dart';
import 'package:vigia_ui/domain/ui_models/device_ui.dart';

part 'devices_provider.g.dart';

class DevicesState {
  final String? errorMessage;
  final ErrorCodes? errorCode;
  final List<DeviceUIModel> devices;

  DevicesState({this.errorMessage, this.errorCode, this.devices = const []});
}

@Riverpod(keepAlive: true)
class Devices extends _$Devices {
  @override
  Future<List<DeviceUIModel>> build() {
    return _loadDevices();
  }

  Future<void> refresh({bool withDelay = true}) async {
    state = await AsyncValue.guard(
      () async => await _loadDevices(withDelay: withDelay),
    );
  }

  Future<void> updateDevice(
    String deviceId, {
    String? nickname,
    DeviceRooms? room,
    bool? isClipsEnabled,
  }) async {
    await ref
        .read(devicesRepositoryProvider)
        .updateDevice(
          deviceId,
          nickname: nickname,
          room: room,
          isClipsEnabled: isClipsEnabled,
        );

    final current = state.asData?.value;
    if (current == null) {
      await refresh(withDelay: false);
      return;
    }

    state = AsyncValue.data([
      for (final device in current)
        if (device.id == deviceId)
          device.copyWith(
            nickname: nickname,
            room: room,
            isClipsEnabled: isClipsEnabled,
          )
        else
          device,
    ]);
  }

  Future<List<DeviceUIModel>> _loadDevices({bool withDelay = true}) async {
    try {
      if (withDelay) {
        await Future.delayed(
          const Duration(milliseconds: 1000),
        ); //Delay para esperar a animação de transição se concluída antes de realizar o carregamento dos dispositivos
      }

      final devices = await ref.read(devicesRepositoryProvider).getDevices();

      final String userId = await TokenStorageService().getUserId();

      final List<DeviceUIModel> result = devices
          .map((device) => DeviceUIModel.fromDTO(device, userId))
          .toList();

      return result;
    } catch (e) {
      rethrow;
    }
  }
}

@riverpod
void addDevice(Ref ref, NewDevice newDevice) {
  final current = ref.read(devicesProvider.notifier).state.asData?.value ?? [];
  
}
