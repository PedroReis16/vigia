import 'dart:io';

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

    final canScan = await WiFiScan.instance.canStartScan(askPermissions: true);
    if (canScan != CanStartScan.yes) {
      throw StateError(_scanBlockedMessage(canScan));
    }

    final started = await WiFiScan.instance.startScan();
    if (!started) {
      throw StateError('Não foi possível iniciar a busca por redes Wi‑Fi.');
    }

    await Future<void>.delayed(const Duration(milliseconds: 1500));

    final canRead = await WiFiScan.instance.canGetScannedResults(
      askPermissions: true,
    );
    if (canRead != CanGetScannedResults.yes) {
      throw StateError(_readBlockedMessage(canRead));
    }

    final accessPoints = await WiFiScan.instance.getScannedResults();
    return _dedupeAndSort(accessPoints);
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
      CanGetScannedResults.noLocationServiceDisabled =>
        'Ative os serviços de localização para listar redes Wi‑Fi.',
      CanGetScannedResults.notSupported =>
        'Listagem de redes Wi‑Fi não suportada neste dispositivo.',
      _ => 'Não foi possível listar redes Wi‑Fi ($reason).',
    };
  }
}
