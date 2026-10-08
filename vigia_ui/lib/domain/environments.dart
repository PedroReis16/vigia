import 'package:flutter_dotenv/flutter_dotenv.dart';

class Environments {
  static final String apiUrl = dotenv.env["API_URL"] ?? "";

  static final String streamBaseUrl =
      (dotenv.env["STREAM_BASE_URL"] ?? "http://localhost:81").replaceAll(
        RegExp(r'/+$'),
        '',
      );

  static String get keycloakUrl =>
      (dotenv.env["KEYCLOAK_URL"] ?? "").replaceAll(RegExp(r'/+$'), '');

  static String get keycloakRealm => dotenv.env["KEYCLOAK_REALM"] ?? "vigia";

  static String get keycloakClientId =>
      dotenv.env["KEYCLOAK_CLIENT_ID"] ?? "vigia-app";
}
