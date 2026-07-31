import 'dart:async';

import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:uuid/uuid.dart';
import 'package:vigia_ui/data/services/app_identity_service.dart';
import 'package:vigia_ui/data/services/ble_pairing_service.dart';
import 'package:vigia_ui/domain/DTOs/device.dart';
import 'package:vigia_ui/domain/DTOs/device_identity.dart';
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
  final AppIdentityService _identity = AppIdentityService();

  StreamSubscription<ScanResult>? _scanSubscription;
  BluetoothDevice? _connectedBleDevice;
  DeviceIdentity? _deviceIdentity;
  String? _bleName;
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
      _scanSubscription = _ble.scanForVigia().listen(_onDeviceFound);
    } catch (error) {
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
      await _ble.provision(
        device,
        ssid: ssid.trim(),
        password: password,
        apiToken: Environments.apiUrl,
      );

      state = DevicePairingState(
        stage: DevicePairingStage.connected,
        device: Device(
          id: identity.deviceId,
          nickname: _bleName ?? 'Vigia',
          ownerId: Uuid().v4(),
        ),
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

      state = const DevicePairingState(stage: DevicePairingStage.provisioning);
    } catch (error) {
      state = DevicePairingState(
        stage: DevicePairingStage.error,
        errorMessage: 'Não foi possível autenticar: $error',
      );
    }
  }

  Future<void> _cleanup() async {
    await _scanSubscription?.cancel();
    _scanSubscription = null;
    await _ble.disconnect(_connectedBleDevice);
    _connectedBleDevice = null;
    _deviceIdentity = null;
    _bleName = null;
  }
}
