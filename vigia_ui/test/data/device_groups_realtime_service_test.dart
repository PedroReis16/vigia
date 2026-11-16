import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/data/services/device_groups_realtime_service.dart';
import 'package:vigia_ui/data/services/keycloak_auth_client.dart';

import '../helpers/fake_token_storage.dart';

void main() {
  test('a failed Keycloak refresh drops the local session', () async {
    final dio = Dio();
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          handler.reject(
            DioException(
              requestOptions: options,
              response: Response(requestOptions: options, statusCode: 400),
            ),
          );
        },
      ),
    );

    var cleared = false;
    final service = DeviceGroupsRealtimeService(
      tokenStorage: FakeTokenStorage(
        accessToken: _expiredAccessToken(),
        refreshToken: 'stale-refresh',
      ),
      keycloak: KeycloakAuthClient(dio, realm: 'vigia', clientId: 'vigia-app'),
      onRefreshFailed: () async {
        cleared = true;
      },
    );

    await service.connect();

    expect(cleared, isTrue);
    expect(service.isConnected, isFalse);
  });
}

String _expiredAccessToken() {
  String encode(String json) =>
      base64Url.encode(utf8.encode(json)).replaceAll('=', '');

  return '${encode('{"alg":"none"}')}.${encode('{"exp":1}')}.sig';
}
