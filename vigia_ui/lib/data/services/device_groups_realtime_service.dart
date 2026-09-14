import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:jwt_decoder/jwt_decoder.dart';
import 'package:signalr_netcore/signalr_client.dart';
import 'package:vigia_ui/data/services/token_storage_service.dart';
import 'package:vigia_ui/domain/DTOs/group_membership_changed.dart';
import 'package:vigia_ui/domain/environments.dart';

typedef GroupMembershipHandler = void Function(GroupMembershipChanged event);

/// Thin wrapper around the ASP.NET Core SignalR device-groups hub.
class DeviceGroupsRealtimeService {
  DeviceGroupsRealtimeService({
    required this._tokenStorage,
    required this._refreshDio,
  });

  final TokenStorageService _tokenStorage;
  final Dio _refreshDio;
  static const _hubPath = '/hubs/device-groups';
  static const _membershipChangedEvent = 'GroupMembershipChanged';
  HubConnection? _connection;
  final _handlers = <GroupMembershipHandler>{};

  bool get isConnected => _connection?.state == HubConnectionState.Connected;

  void addHandler(GroupMembershipHandler handler) => _handlers.add(handler);

  void removeHandler(GroupMembershipHandler handler) =>
      _handlers.remove(handler);

  Future<void> connect() async {
    if (_connection != null &&
        (_connection!.state == HubConnectionState.Connected ||
            _connection!.state == HubConnectionState.Connecting ||
            _connection!.state == HubConnectionState.Reconnecting)) {
      return;
    }

    await disconnect();

    final token = await _ensureAccessToken();
    if (token.isEmpty) {
      debugPrint('[SignalR] skip connect: no access token');
      return;
    }

    final hubUrl = '${Environments.apiUrl}$_hubPath';
    debugPrint('[SignalR] connecting to $hubUrl');

    final connection = HubConnectionBuilder()
        .withUrl(
          hubUrl,
          options: HttpConnectionOptions(
            accessTokenFactory: _ensureAccessToken,
          ),
        )
        .withAutomaticReconnect(retryDelays: [0, 2000, 5000, 10000, 30000])
        .build();

    connection.on(_membershipChangedEvent, _onMembershipChanged);
    connection.onclose(({Exception? error}) {
      debugPrint('[SignalR] closed: $error');
    });
    connection.onreconnected(({String? connectionId}) {
      debugPrint('[SignalR] reconnected: $connectionId');
    });

    _connection = connection;
    await connection.start();
    debugPrint('[SignalR] connected');
  }

  Future<void> disconnect() async {
    final connection = _connection;
    _connection = null;
    if (connection == null) return;

    try {
      connection.off(_membershipChangedEvent);
      await connection.stop();
    } catch (_) {}
  }

  Future<String> _ensureAccessToken() async {
    final current = await _tokenStorage.getAccessToken();
    if (current != null &&
        current.isNotEmpty &&
        !JwtDecoder.isExpired(current)) {
      return current;
    }

    final refreshToken = await _tokenStorage.getRefreshToken();
    if (refreshToken == null || refreshToken.isEmpty) {
      return current ?? '';
    }

    try {
      final response = await _refreshDio.post(
        '/auth/refresh',
        data: {'refreshToken': refreshToken},
      );
      final newAccess = response.data['accessToken'] as String;
      final newRefresh = response.data['refreshToken'] as String;
      await _tokenStorage.saveUserTokens(newAccess, newRefresh);
      return newAccess;
    } catch (e) {
      debugPrint('[SignalR] token refresh failed: $e');
      return current ?? '';
    }
  }

  void _onMembershipChanged(List<Object?>? args) {
    debugPrint('[SignalR] GroupMembershipChanged raw=$args');
    if (args == null || args.isEmpty) return;

    final event = GroupMembershipChanged.tryParse(args.first);
    if (event == null) {
      debugPrint('[SignalR] failed to parse membership event');
      return;
    }

    for (final handler in List<GroupMembershipHandler>.from(_handlers)) {
      handler(event);
    }
  }
}
