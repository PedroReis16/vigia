import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'pending_invite_provider.g.dart';

const pendingInviteStorageKey = 'vigia.pending_invite_token';

/// Replaced in tests. Production reads and writes secure storage.
@visibleForTesting
PendingInviteStore? pendingInviteStoreOverride;

abstract class PendingInviteStore {
  Future<String?> read();
  Future<void> write(String token);
  Future<void> delete();
}

class MemoryPendingInviteStore implements PendingInviteStore {
  String? value;

  @override
  Future<void> delete() async => value = null;

  @override
  Future<String?> read() async => value;

  @override
  Future<void> write(String token) async => value = token;
}

class SecurePendingInviteStore implements PendingInviteStore {
  SecurePendingInviteStore([FlutterSecureStorage? storage])
    : _storage = storage ?? const FlutterSecureStorage();

  final FlutterSecureStorage _storage;

  @override
  Future<void> delete() async {
    try {
      await _storage.delete(key: pendingInviteStorageKey);
    } catch (_) {}
  }

  @override
  Future<String?> read() async {
    try {
      return await _storage.read(key: pendingInviteStorageKey);
    } catch (_) {
      return null;
    }
  }

  @override
  Future<void> write(String token) async {
    try {
      await _storage.write(key: pendingInviteStorageKey, value: token);
    } catch (_) {}
  }
}

PendingInviteStore get pendingInviteStore =>
    pendingInviteStoreOverride ?? SecurePendingInviteStore();

@Riverpod(keepAlive: true)
class PendingInviteToken extends _$PendingInviteToken {
  @override
  String? build() {
    unawaited(_restore());
    return null;
  }

  Future<void> _restore() async {
    final stored = await pendingInviteStore.read();
    if (!ref.mounted || state != null) return;
    if (stored != null && stored.isNotEmpty) state = stored;
  }

  void setToken(String? token) {
    state = token;
    if (token == null || token.isEmpty) {
      unawaited(pendingInviteStore.delete());
      return;
    }
    unawaited(pendingInviteStore.write(token));
  }

  void clear() {
    state = null;
    unawaited(pendingInviteStore.delete());
  }
}
