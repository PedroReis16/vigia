import 'dart:io';

import 'package:permission_handler/permission_handler.dart';
import 'package:vigia_ui/domain/DTOs/wifi_network.dart';
import 'package:wifi_scan/wifi_scan.dart';

/// Scans nearby Wi‑Fi networks on the phone.
///
/// Full scan is supported on Android. iOS has no public scan API — callers
/// should fall back to manual SSID entry when [isScanSupported] is false.
class WifiScanService {
  bool get isScanSupported => Platform.isAndroid;

  Future<List<WifiNetwork>> scanNearbyNetworks() async {
    if (!isScanSupported) {
      return const [];
    }

    await _ensureScanPermissions();

    // Permissions are requested above; avoid a second native dialog.
    final canScan = await WiFiScan.instance.canStartScan(askPermissions: false);
    if (canScan != CanStartScan.yes) {
      throw StateError(_scanBlockedMessage(canScan));
    }

    final started = await WiFiScan.instance.startScan();
    if (!started) {
      throw StateError('Não foi possível iniciar a busca por redes Wi‑Fi.');
    }

    await Future<void>.delayed(const Duration(milliseconds: 1500));

    final canRead = await WiFiScan.instance.canGetScannedResults(
      askPermissions: false,
    );
    if (canRead != CanGetScannedResults.yes) {
      throw StateError(_readBlockedMessage(canRead));
    }

    final accessPoints = await WiFiScan.instance.getScannedResults();
    return _dedupeAndSort(accessPoints);
  }

  /// Requests the runtime permissions required for Wi‑Fi scan on this Android
  /// version. Android 13+ uses [Permission.nearbyWifiDevices]; older versions
  /// need precise location while in use.
  Future<void> _ensureScanPermissions() async {
    if (!Platform.isAndroid) return;

    final nearby = await Permission.nearbyWifiDevices.status;
    if (nearby != PermissionStatus.denied &&
        nearby != PermissionStatus.permanentlyDenied) {
      if (nearby.isGranted) return;

      final requested = await Permission.nearbyWifiDevices.request();
      if (requested.isGranted) return;
    }

    var location = await Permission.locationWhenInUse.status;
    if (!location.isGranted) {
      location = await Permission.locationWhenInUse.request();
    }
    if (!location.isGranted) {
      throw StateError(
        'Ative a permissão de localização para buscar redes Wi‑Fi.',
      );
    }

    if (!await Permission.location.serviceStatus.isEnabled) {
      throw StateError(
        'Ative os serviços de localização para buscar redes Wi‑Fi.',
      );
    }
  }

  List<WifiNetwork> _dedupeAndSort(List<WiFiAccessPoint> accessPoints) {
    final bySsid = <String, WifiNetwork>{};

    for (final ap in accessPoints) {
      final ssid = ap.ssid.trim();
      if (ssid.isEmpty || ssid == '<unknown ssid>') continue;

      final network = WifiNetwork(
        ssid: ssid,
        signalLevel: ap.level,
        isSecure: _isSecure(ap.capabilities),
      );

      final existing = bySsid[ssid];
      if (existing == null || network.signalLevel > existing.signalLevel) {
        bySsid[ssid] = network;
      }
    }

    final networks = bySsid.values.toList()
      ..sort((a, b) => b.signalLevel.compareTo(a.signalLevel));
    return networks;
  }

  bool _isSecure(String capabilities) {
    final caps = capabilities.toUpperCase();
    return caps.contains('WEP') ||
        caps.contains('WPA') ||
        caps.contains('PSK') ||
        caps.contains('EAP');
  }

  String _scanBlockedMessage(CanStartScan reason) {
    return switch (reason) {
      CanStartScan.noLocationPermissionRequired ||
      CanStartScan.noLocationPermissionDenied =>
        'Ative a permissão de localização para buscar redes Wi‑Fi.',
      CanStartScan.noLocationPermissionUpgradeAccuracy =>
        'Ative a localização precisa nas configurações do app para buscar redes Wi‑Fi.',
      CanStartScan.noLocationServiceDisabled =>
        'Ative os serviços de localização para buscar redes Wi‑Fi.',
      CanStartScan.notSupported =>
        'Busca de redes Wi‑Fi não suportada neste dispositivo.',
      _ => 'Não foi possível buscar redes Wi‑Fi ($reason).',
    };
  }

  String _readBlockedMessage(CanGetScannedResults reason) {
    return switch (reason) {
      CanGetScannedResults.noLocationPermissionRequired ||
      CanGetScannedResults.noLocationPermissionDenied =>
        'Ative a permissão de localização para listar redes Wi‑Fi.',
      CanGetScannedResults.noLocationPermissionUpgradeAccuracy =>
        'Ative a localização precisa nas configurações do app para listar redes Wi‑Fi.',
      CanGetScannedResults.noLocationServiceDisabled =>
        'Ative os serviços de localização para listar redes Wi‑Fi.',
      CanGetScannedResults.notSupported =>
        'Listagem de redes Wi‑Fi não suportada neste dispositivo.',
      _ => 'Não foi possível listar redes Wi‑Fi ($reason).',
    };
  }
}
