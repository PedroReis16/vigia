import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/data/services/keycloak_authorize.dart';

void main() {
  test('authorize URL carries PKCE, the fixed redirect and the client', () {
    final uri = KeycloakAuthorize.build(
      baseUrl: 'http://10.0.0.55/auth/',
      realm: 'vigia',
      clientId: 'vigia-app',
      codeChallenge: 'challenge-value',
      state: 'state-value',
    );

    expect(uri.origin, 'http://10.0.0.55');
    expect(uri.path, '/auth/realms/vigia/protocol/openid-connect/auth');
    expect(uri.queryParameters['client_id'], 'vigia-app');
    expect(uri.queryParameters['redirect_uri'], 'vigia://auth/callback');
    expect(uri.queryParameters['response_type'], 'code');
    expect(uri.queryParameters['scope'], 'openid offline_access');
    expect(uri.queryParameters['code_challenge'], 'challenge-value');
    expect(uri.queryParameters['code_challenge_method'], 'S256');
    expect(uri.queryParameters['state'], 'state-value');
  });

  test('PKCE challenge is the S256 digest of the verifier', () {
    const verifier = 'abcdefghijklmnopqrstuvwxyzABCDEF';
    final challenge = Pkce.challengeFor(verifier);

    expect(challenge, isNot(contains('=')));
    expect(challenge, isNot(contains('+')));
    expect(challenge, isNot(contains('/')));
    expect(challenge, Pkce.challengeFor(verifier));
    expect(challenge.length, greaterThan(40));
  });

  test('callback parse reads code and state', () {
    final callback = KeycloakCallback.tryParse(
      Uri.parse('vigia://auth/callback?code=abc&state=xyz'),
    );

    expect(callback, isNotNull);
    expect(callback!.isSuccess, isTrue);
    expect(callback.code, 'abc');
    expect(callback.state, 'xyz');
    expect(callback.error, isNull);
  });

  test('callback parse reads the error and is not a success', () {
    final callback = KeycloakCallback.tryParse(
      Uri.parse('vigia://auth/callback?error=access_denied&state=xyz'),
    );

    expect(callback, isNotNull);
    expect(callback!.isSuccess, isFalse);
    expect(callback.error, 'access_denied');
    expect(callback.code, isNull);
  });

  test('callback parse ignores urls that are not the app redirect', () {
    expect(
      KeycloakCallback.tryParse(Uri.parse('vigia://invite/code-1')),
      isNull,
    );
    expect(
      KeycloakCallback.tryParse(
        Uri.parse('https://example.com/auth/callback?code=abc'),
      ),
      isNull,
    );
  });
}
