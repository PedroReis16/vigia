import 'dart:async';
import 'dart:io';

import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:permission_handler/permission_handler.dart';

/// BLE client for the Vigia register beacon (GATT peripheral on the device).
class BlePairingService {
  BlePairingService();

  /// Matches [SERVICE_UID] in vigia-fall/connection/runner.py
  static final Guid serviceUuid = Guid(
    '87fa2616-1953-4d5a-80d6-40201b9347eb',
  );

  static final Guid writeCharUuid = Guid(
    '14159635-68c6-4738-a066-9021e60d1efe',
  );

  static final Guid notifyCharUuid = Guid(
    '24159635-68c6-4738-a066-9021e60d1eff',
  );

  Future<void> ensureReady() async {
    await _requestPermissions();

    if (await FlutterBluePlus.isSupported == false) {
      throw StateError('Bluetooth LE não é suportado neste dispositivo.');
    }

    final adapterState = await FlutterBluePlus.adapterState.first;
    if (adapterState != BluetoothAdapterState.on) {
      if (Platform.isAndroid) {
        await FlutterBluePlus.turnOn();
      } else {
        throw StateError(
          'Ative o Bluetooth nas configurações para continuar.',
        );
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
            final id = result.device.remoteId.str;
            if (seen.add(id)) {
              controller.add(result);
            }
          }
        });

        // Keep (re)starting the scan until the caller cancels.
        while (!cancelled && !controller.isClosed) {
          try {
            await FlutterBluePlus.startScan(withServices: [serviceUuid]);
            await FlutterBluePlus.isScanning
                .where((scanning) => !scanning)
                .first;
            if (!cancelled && !controller.isClosed) {
              await Future<void>.delayed(const Duration(milliseconds: 400));
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

  Future<void> connect(BluetoothDevice device) async {
    await FlutterBluePlus.stopScan();
    await device.connect(
      license: License.nonprofit,
      timeout: const Duration(seconds: 20),
      autoConnect: false,
    );
    await device.discoverServices();
  }

  Future<void> disconnect(BluetoothDevice? device) async {
    await FlutterBluePlus.stopScan();
    if (device == null) return;
    try {
      await device.disconnect();
    } catch (_) {}
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
