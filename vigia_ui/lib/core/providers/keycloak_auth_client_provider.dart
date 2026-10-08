import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vigia_ui/data/services/keycloak_auth_client.dart';
import 'package:vigia_ui/data/services/keycloak_browser_session.dart';
import 'package:vigia_ui/domain/environments.dart';

final keycloakAuthClientProvider = Provider<KeycloakAuthClient>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: Environments.keycloakUrl,
      contentType: Headers.formUrlEncodedContentType,
    ),
  );
  ref.onDispose(() => dio.close());
  return KeycloakAuthClient(
    dio,
    realm: Environments.keycloakRealm,
    clientId: Environments.keycloakClientId,
  );
});

final keycloakBrowserSessionProvider = Provider<KeycloakBrowserSession>(
  (ref) => KeycloakBrowserSession(),
);
