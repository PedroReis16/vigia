import 'dart:convert';

import 'package:cryptography/cryptography.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Local Ed25519 identity used to prove the app during BLE challenge.
class AppIdentityService {
  AppIdentityService({FlutterSecureStorage? storage})
    : _storage = storage ?? const FlutterSecureStorage();

  static const _privateKeyStorageKey = 'vigia_app_ed25519_private_key';

  final FlutterSecureStorage _storage;
  final Ed25519 _algorithm = Ed25519();

  SimpleKeyPair? _cachedKeyPair;

  Future<SimpleKeyPair> getOrCreateKeyPair() async {
    if (_cachedKeyPair != null) return _cachedKeyPair!;

    final stored = await _storage.read(key: _privateKeyStorageKey);
    if (stored != null && stored.isNotEmpty) {
      final seed = base64Decode(stored);
      _cachedKeyPair = await _algorithm.newKeyPairFromSeed(seed);
      return _cachedKeyPair!;
    }

    final keyPair = await _algorithm.newKeyPair();
    final seed = await keyPair.extractPrivateKeyBytes();
    await _storage.write(key: _privateKeyStorageKey, value: base64Encode(seed));
    _cachedKeyPair = keyPair;
    return keyPair;
  }

  Future<String> publicKeyHex() async {
    final keyPair = await getOrCreateKeyPair();
    final publicKey = await keyPair.extractPublicKey();
    return _toHex(publicKey.bytes);
  }

  Future<String> signHex(List<int> message) async {
    final keyPair = await getOrCreateKeyPair();
    final signature = await _algorithm.sign(message, keyPair: keyPair);
    return _toHex(signature.bytes);
  }

  static String _toHex(List<int> bytes) {
    final buffer = StringBuffer();
    for (final byte in bytes) {
      buffer.write(byte.toRadixString(16).padLeft(2, '0'));
    }
    return buffer.toString();
  }
}
