import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:vigia_ui/core/providers/token_storage_provider.dart';
import 'package:vigia_ui/data/services/device_groups_realtime_service.dart';
import 'package:vigia_ui/domain/DTOs/group_membership_changed.dart';
import 'package:vigia_ui/domain/environments.dart';
import 'package:vigia_ui/presentation/devices/providers/device_details_provider.dart';
import 'package:vigia_ui/presentation/devices/providers/devices_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';

part 'device_groups_realtime_provider.g.dart';

@Riverpod(keepAlive: true)
DeviceGroupsRealtimeService deviceGroupsRealtimeService(Ref ref) {
  // Dedicated Dio without auth interceptor — refresh endpoint is public.
  final refreshDio = Dio(BaseOptions(baseUrl: Environments.apiUrl));
  final service = DeviceGroupsRealtimeService(
    tokenStorage: ref.watch(tokenStorageProvider),
    refreshDio: refreshDio,
  );
  ref.onDispose(() {
    unawaited(service.disconnect());
  });
  return service;
}

/// Keeps the SignalR connection alive while the user is authenticated and
/// refreshes device/user lists when group membership changes.
@Riverpod(keepAlive: true)
class DeviceGroupsRealtimeBridge extends _$DeviceGroupsRealtimeBridge {
  GroupMembershipHandler? _handler;

  @override
  void build() {
    final service = ref.watch(deviceGroupsRealtimeServiceProvider);

    _handler = _onEvent;
    service.addHandler(_handler!);
    ref.onDispose(() {
      if (_handler != null) service.removeHandler(_handler!);
    });

    ref.listen(authSessionProvider, (previous, next) {
      next.whenData((loggedIn) {
        if (loggedIn) {
          unawaited(_connect(service));
        } else {
          unawaited(service.disconnect());
        }
      });
    }, fireImmediately: true);
  }

  Future<void> _connect(DeviceGroupsRealtimeService service) async {
    try {
      await service.connect();
    } catch (e, st) {
      debugPrint('[SignalR] connect failed: $e\n$st');
    }
  }

  Future<void> _onEvent(GroupMembershipChanged event) async {
    debugPrint(
      '[SignalR] applying ${event.changeType} for user ${event.affectedUserId} '
      'devices=${event.deviceIds}',
    );

    if (event.deviceIds.isEmpty) {
      ref.invalidate(getDeviceUsersProvider);
    } else {
      for (final deviceId in event.deviceIds) {
        ref.invalidate(getDeviceUsersProvider(deviceId));
      }
    }

    try {
      await ref.read(devicesProvider.notifier).refresh(withDelay: false);
    } catch (e) {
      debugPrint('[SignalR] devices refresh failed: $e');
    }
  }
}
