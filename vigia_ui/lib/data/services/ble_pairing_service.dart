import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:vigia_ui/domain/DTOs/device_identity.dart';
import 'package:vigia_ui/domain/constants.dart';

/// BLE client for the Vigia register beacon (GATT peripheral on the device).
class BlePairingService {
  BlePairingService();

  Future<void> ensureReady() async {
    await _requestPermissions();

    if (await FlutterBluePlus.isSupported == false) {
      throw StateError('Bluetooth LE não é suportado neste dispositivo.');
    }

    final adapterState = await FlutterBluePlus.adapterState.first;
    if (adapterState != BluetoothAdapterState.on) {
      if (Platform.isAndroid) {
        await FlutterBluePlus.turnOn();
        await FlutterBluePlus.adapterState
            .where((state) => state == BluetoothAdapterState.on)
            .first;
      } else {
        throw StateError('Ative o Bluetooth nas configurações para continuar.');
      }
    }
  }

  /// Continuous scan until the returned stream is cancelled.
  /// Does not time out — keeps looking while the modal is open.
  Stream<ScanResult> scanForVigia() {
    late final StreamController<ScanResult> controller;
    StreamSubscription<List<ScanResult>>? resultsSubscription;
    var cancelled = false;
    final seen = <String>{};

    controller = StreamController<ScanResult>(
      onListen: () async {
        await FlutterBluePlus.stopScan();
        resultsSubscription = FlutterBluePlus.onScanResults.listen((results) {
          for (final result in results) {
            if (!_isVigiaAdvertisement(result)) continue;

            final id = result.device.remoteId.str;
            if (seen.add(id)) {
              controller.add(result);
            }
          }
        });

        // Keep (re)starting the scan until the caller cancels.
        // Do not use [withServices]: Bless often exposes the GATT service only
        // after connect and does not put the UUID in the advertisement packet.
        while (!cancelled && !controller.isClosed) {
          try {
            await FlutterBluePlus.startScan(
              timeout: const Duration(seconds: 15),
              androidScanMode: AndroidScanMode.lowLatency,
            );
            await FlutterBluePlus.isScanning
                .where((scanning) => !scanning)
                .first;
            if (!cancelled && !controller.isClosed) {
              await Future<void>.delayed(const Duration(seconds: 2));
            }
          } catch (_) {
            if (cancelled || controller.isClosed) break;
            await Future<void>.delayed(const Duration(seconds: 1));
          }
        }
      },
      onCancel: () async {
        cancelled = true;
        await resultsSubscription?.cancel();
        await FlutterBluePlus.stopScan();
      },
    );

    return controller.stream;
  }

  /// Matches advertised name (Vigia-…) and/or service UUID when present in AD.
  bool _isVigiaAdvertisement(ScanResult result) {
    final adv = result.advertisementData;
    final name =
        (adv.advName.isNotEmpty ? adv.advName : result.device.platformName)
            .trim();

    if (name.toLowerCase().startsWith(
      Constants.deviceNamePrefix.toLowerCase(),
    )) {
      return true;
    }

    final target = Constants.serviceConnectionUuid.str.toLowerCase();
    return adv.serviceUuids.any((uuid) => uuid.str.toLowerCase() == target);
  }

  Future<void> connect(BluetoothDevice device) async {
    await FlutterBluePlus.stopScan();
    await device.connect(
      license: License.nonprofit,
      timeout: const Duration(seconds: 20),
      autoConnect: false,
    );
    await device.discoverServices();
  }

  Future<DeviceIdentity> readIdentity(BluetoothDevice device) async {
    final characteristic = await _requireCharacteristic(
      device,
      Constants.charIdentityUuid,
    );
    final bytes = await characteristic.read();
    final jsonMap = jsonDecode(utf8.decode(bytes)) as Map<String, dynamic>;
    return DeviceIdentity.fromJson(jsonMap);
  }

  /// Reads a nonce, signs it with [signNonce], writes enroll/auth JSON, expects VALIDATED.
  Future<void> authenticate(
    BluetoothDevice device, {
    required String appSignPubHex,
    required Future<String> Function(List<int> nonceBytes) signNonce,
  }) async {
    final characteristic = await _requireCharacteristic(
      device,
      Constants.charChallengeUuid,
    );

    final nonceHex = utf8.decode(await characteristic.read()).trim();
    final nonceBytes = _hexToBytes(nonceHex);
    final signatureHex = await signNonce(nonceBytes);

    final payload = jsonEncode({
      'app_sign_pub': appSignPubHex,
      'signature': signatureHex,
    });

    await characteristic.write(
      utf8.encode(payload),
      withoutResponse: false,
      allowLongWrite: true,
    );

    final status = utf8.decode(await characteristic.read()).trim();
    if (status != 'VALIDATED') {
      throw StateError('Desafio BLE rejeitado: $status');
    }
  }

  Future<void> provision(
    BluetoothDevice device, {
    required String ssid,
    required String password,
    String apiToken = "ASDBASDA",
  }) async {
    final characteristic = await _requireCharacteristic(
      device,
      Constants.charProvisionUuid,
    );

    final payload = jsonEncode({
      'ssid': ssid,
      'password': password,
      'api_token': apiToken,
    });

    await characteristic.write(
      utf8.encode(payload),
      withoutResponse: false,
      allowLongWrite: true,
    );

    final status = utf8.decode(await characteristic.read()).trim();
    if (status != 'SUCCESS') {
      throw StateError('Provisionamento BLE falhou: $status');
    }
  }

  Future<void> disconnect(BluetoothDevice? device) async {
    await FlutterBluePlus.stopScan();
    if (device == null) return;
    try {
      await device.disconnect();
    } catch (_) {}
  }

  Future<BluetoothCharacteristic> _requireCharacteristic(
    BluetoothDevice device,
    Guid characteristicUuid,
  ) async {
    final services = device.servicesList.isEmpty
        ? await device.discoverServices()
        : device.servicesList;

    final targetService = Constants.serviceConnectionUuid.str.toLowerCase();
    final targetChar = characteristicUuid.str.toLowerCase();

    for (final service in services) {
      if (service.uuid.str.toLowerCase() != targetService) continue;
      for (final characteristic in service.characteristics) {
        if (characteristic.uuid.str.toLowerCase() == targetChar) {
          return characteristic;
        }
      }
    }

    throw StateError(
      'Characteristic $targetChar não encontrada no serviço Vigia.',
    );
  }

  List<int> _hexToBytes(String hex) {
    final normalized = hex.replaceAll(RegExp(r'\s+'), '');
    if (normalized.length.isOdd) {
      throw FormatException('Nonce hex inválido: $hex');
    }
    final bytes = <int>[];
    for (var i = 0; i < normalized.length; i += 2) {
      bytes.add(int.parse(normalized.substring(i, i + 2), radix: 16));
    }
    return bytes;
  }

  Future<void> _requestPermissions() async {
    if (!Platform.isAndroid) return;

    final permissions = <Permission>[
      Permission.bluetoothScan,
      Permission.bluetoothConnect,
    ];

    // Location is still required for BLE scan on Android 11 and below.
    if (await Permission.locationWhenInUse.isDenied ||
        await Permission.locationWhenInUse.isRestricted) {
      permissions.add(Permission.locationWhenInUse);
    }

    final statuses = await permissions.request();
    final denied = statuses.entries.where((e) => !e.value.isGranted);
    if (denied.isNotEmpty) {
      throw StateError(
        'Permissões de Bluetooth necessárias para encontrar o Vigia.',
      );
    }
  }
}
