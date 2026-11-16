import 'dart:async';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/data/interceptors/auth_interceptor.dart';
import 'package:vigia_ui/data/services/keycloak_auth_client.dart';

import '../helpers/fake_token_storage.dart';

class _CountingAdapter implements HttpClientAdapter {
  int inFlight = 0;
  int maxInFlight = 0;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    inFlight++;
    if (inFlight > maxInFlight) maxInFlight = inFlight;
    await Future<void>.delayed(const Duration(milliseconds: 30));
    inFlight--;
    return ResponseBody.fromString(
      '{}',
      200,
      headers: {
        Headers.contentTypeHeader: ['application/json'],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  test('successful API calls run in parallel', () async {
    final adapter = _CountingAdapter();
    final dio = Dio(BaseOptions(baseUrl: 'https://api.test'));
    dio.httpClientAdapter = adapter;
    dio.interceptors.add(
      AuthInterceptor(
        dio: dio,
        keycloak: KeycloakAuthClient(
          Dio(),
          realm: 'vigia',
          clientId: 'vigia-app',
        ),
        tokenStorage: FakeTokenStorage(accessToken: 'access'),
        onRefreshFailed: () async {},
      ),
    );

    await Future.wait([
      dio.get<Object>('/users/me'),
      dio.get<Object>('/devices/list'),
    ]);

    expect(adapter.maxInFlight, 2);
  });
}
