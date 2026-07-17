import 'dart:async';

import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:uuid/uuid.dart';
import 'package:vigia_ui/data/services/ble_pairing_service.dart';
import 'package:vigia_ui/domain/DTOs/device.dart';
import 'package:vigia_ui/domain/enums/device_pairing_stage.dart';

part 'device_pairing_provider.g.dart';

class DevicePairingState {
  const DevicePairingState({
    required this.stage,
    this.device,
    this.errorMessage,
  });

  final DevicePairingStage stage;
  final Device? device;
  final String? errorMessage;

  DevicePairingState copyWith({
    DevicePairingStage? stage,
    Device? device,
    String? errorMessage,
  }) {
    return DevicePairingState(
      stage: stage ?? this.stage,
      device: device ?? this.device,
      errorMessage: errorMessage,
    );
  }
}

@riverpod
class DevicePairing extends _$DevicePairing {
  final BlePairingService _ble = BlePairingService();
  StreamSubscription<ScanResult>? _scanSubscription;
  BluetoothDevice? _connectedBleDevice;
  var _started = false;

  @override
  DevicePairingState build() {
    ref.onDispose(_cleanup);
    return const DevicePairingState(stage: DevicePairingStage.scanning);
  }

  Future<void> start() async {
    if (_started) return;
    _started = true;

    state = const DevicePairingState(stage: DevicePairingStage.scanning);

    try {
      await _ble.ensureReady();
      await _scanSubscription?.cancel();
      // Keep scanning while the modal is open — no timeout / "not found" error.
      _scanSubscription = _ble.scanForVigia().listen(_onDeviceFound);
    } catch (error) {
      // Permissions / Bluetooth off — user must fix before scanning can continue.
      state = DevicePairingState(
        stage: DevicePairingStage.error,
        errorMessage: error.toString(),
      );
    }
  }

  Future<void> retry() async {
    await _cleanup();
    _started = false;
    await start();
  }

  Future<void> _onDeviceFound(ScanResult result) async {
    if (state.stage != DevicePairingStage.scanning) return;

    await _scanSubscription?.cancel();
    _scanSubscription = null;

    state = const DevicePairingState(stage: DevicePairingStage.connecting);

    try {
      await _ble.connect(result.device);
      _connectedBleDevice = result.device;

      final name = result.device.platformName.trim().isEmpty
          ? 'Vigia'
          : result.device.platformName.trim();

      state = DevicePairingState(
        stage: DevicePairingStage.connected,
        device: Device(
          id: const Uuid().v4(),
          description: name,
        ),
      );
    } catch (error) {
      state = DevicePairingState(
        stage: DevicePairingStage.error,
        errorMessage: 'Não foi possível conectar: $error',
      );
    }
  }

  Future<void> _cleanup() async {
    await _scanSubscription?.cancel();
    _scanSubscription = null;
    await _ble.disconnect(_connectedBleDevice);
    _connectedBleDevice = null;
  }
}
