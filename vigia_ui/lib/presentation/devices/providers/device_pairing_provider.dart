import 'dart:async';

import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/repository_providers/devices_repository_provider.dart';
import 'package:vigia_ui/data/services/app_identity_service.dart';
import 'package:vigia_ui/data/services/ble_pairing_service.dart';
import 'package:vigia_ui/domain/DTOs/device_identity.dart';
import 'package:vigia_ui/domain/DTOs/new_device.dart';
import 'package:vigia_ui/domain/enums/device_pairing_stage.dart';
import 'package:vigia_ui/domain/environments.dart';

part 'device_pairing_provider.g.dart';

class DevicePairingState {
  const DevicePairingState({
    required this.stage,
    this.device,
    this.errorMessage,
  });

  final DevicePairingStage stage;
  final NewDevice? device;
  final String? errorMessage;

  DevicePairingState copyWith({
    DevicePairingStage? stage,
    NewDevice? device,
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
  final AppIdentityService _identity = AppIdentityService();

  StreamSubscription<ScanResult>? _scanSubscription;
  BluetoothDevice? _connectedBleDevice;
  DeviceIdentity? _deviceIdentity;
  String? _bleName;
  var _started = false;
  var _registered = false;

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
      _scanSubscription = _ble.scanForVigia().listen(_onDeviceFound);
    } catch (error) {
      state = DevicePairingState(
        stage: DevicePairingStage.error,
        errorMessage: error.toString(),
      );
    }
  }

  Future<void> retry() async {
    // Keep BLE session and return to Wi‑Fi form after provision/network errors.
    if (_connectedBleDevice != null &&
        _deviceIdentity != null &&
        _registered) {
      state = const DevicePairingState(stage: DevicePairingStage.provisioning);
      return;
    }

    await _cleanup();
    _started = false;
    await start();
  }

  Future<void> submitWifi({
    required String ssid,
    required String password,
  }) async {
    final device = _connectedBleDevice;
    final identity = _deviceIdentity;
    if (device == null || identity == null) {
      state = const DevicePairingState(
        stage: DevicePairingStage.error,
        errorMessage: 'Sessão BLE inválida. Tente novamente.',
      );
      return;
    }

    if (state.stage != DevicePairingStage.provisioning) return;

    try {
      state = const DevicePairingState(
        stage: DevicePairingStage.testingNetwork,
      );

      await _ble.provision(
        device,
        ssid: ssid.trim(),
        password: password,
        apiBaseUrl: Environments.apiUrl,
      );

      final status = await _ble.pollProvisionStatus(device);

      if (status == 'WIFI_FAIL') {
        state = const DevicePairingState(
          stage: DevicePairingStage.error,
          errorMessage:
              'Não foi possível conectar ao Wi‑Fi. Verifique a rede e a senha e tente novamente.',
        );
        return;
      }

      if (status != 'SUCCESS') {
        state = DevicePairingState(
          stage: DevicePairingStage.error,
          errorMessage: 'Falha no provisionamento: $status',
        );
        return;
      }

      final newDevice = _toNewDevice(identity);

      try {
        await ref.read(devicesRepositoryProvider).trackDevice(newDevice.id);
      } catch (error) {
        state = DevicePairingState(
          stage: DevicePairingStage.error,
          errorMessage: 'Não foi possível vincular o dispositivo: $error',
        );
        return;
      }

      state = DevicePairingState(
        stage: DevicePairingStage.connected,
        device: newDevice,
      );
    } catch (error) {
      state = DevicePairingState(
        stage: DevicePairingStage.error,
        errorMessage: 'Falha no provisionamento: $error',
      );
    }
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
          ? (result.advertisementData.advName.trim().isEmpty
                ? 'Vigia'
                : result.advertisementData.advName.trim())
          : result.device.platformName.trim();
      _bleName = name;

      state = const DevicePairingState(
        stage: DevicePairingStage.authenticating,
      );

      final identity = await _ble.readIdentity(result.device);
      _deviceIdentity = identity;

      final appPub = await _identity.publicKeyHex();
      await _ble.authenticate(
        result.device,
        appSignPubHex: appPub,
        signNonce: _identity.signHex,
      );
    } catch (error) {
      state = DevicePairingState(
        stage: DevicePairingStage.error,
        errorMessage: 'Não foi possível autenticar: $error',
      );
      return;
    }

    try {
      state = const DevicePairingState(stage: DevicePairingStage.registering);

      await _registerDevice(_deviceIdentity!);
      _registered = true;

      state = const DevicePairingState(stage: DevicePairingStage.provisioning);
    } catch (error) {
      state = DevicePairingState(
        stage: DevicePairingStage.error,
        errorMessage: 'Não foi possível registrar o dispositivo: $error',
      );
    }
  }

  Future<void> _registerDevice(DeviceIdentity identity) async {
    final repo = ref.read(devicesRepositoryProvider);
    final newDevice = _toNewDevice(identity);

    final existing = await repo.getDevice(newDevice.id);
    if (existing == null) {
      await repo.registerDevice(newDevice);
    }
  }

  NewDevice _toNewDevice(DeviceIdentity identity) {
    return NewDevice(
      id: identity.deviceId,
      name: identity.name.isNotEmpty ? identity.name : (_bleName ?? 'Vigia'),
      signPublicKey: identity.signPub,
      macAddress: identity.macAddress,
    );
  }

  Future<void> _cleanup() async {
    await _scanSubscription?.cancel();
    _scanSubscription = null;
    await _ble.disconnect(_connectedBleDevice);
    _connectedBleDevice = null;
    _deviceIdentity = null;
    _bleName = null;
    _registered = false;
  }
}
