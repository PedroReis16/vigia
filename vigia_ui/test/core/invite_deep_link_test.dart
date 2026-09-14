import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/core/invite_deep_link.dart';

void main() {
  group('InviteDeepLink.extractToken', () {
    test('parses vigia://invite/{code}', () {
      final uri = Uri.parse('vigia://invite/abc123');
      expect(InviteDeepLink.extractToken(uri), 'abc123');
    });

    test('parses vigia:///invite/{code}', () {
      final uri = Uri.parse('vigia:///invite/xyz789');
      expect(InviteDeepLink.extractToken(uri), 'xyz789');
    });

    test('parses HTTPS public landing /i/{code}', () {
      final uri = Uri.parse('https://example.com/i/token-here');
      expect(InviteDeepLink.extractToken(uri), 'token-here');
    });

    test('parses HTTPS nested path ending in /i/{code}', () {
      final uri = Uri.parse('https://example.com/app/i/nested-code');
      expect(InviteDeepLink.extractToken(uri), 'nested-code');
    });

    test('parses in-app path /invite/{code}', () {
      final uri = Uri.parse('/invite/path-code');
      expect(InviteDeepLink.extractToken(uri), 'path-code');
    });

    test('parses host invite when scheme stripped', () {
      final uri = Uri.parse('//invite/stripped-code');
      expect(InviteDeepLink.extractToken(uri), 'stripped-code');
    });

    test('returns null for invalid URI', () {
      expect(
        InviteDeepLink.extractToken(Uri.parse('https://example.com/other')),
        isNull,
      );
      expect(
        InviteDeepLink.extractToken(Uri.parse('vigia://other/foo')),
        isNull,
      );
      expect(InviteDeepLink.extractToken(Uri.parse('vigia://invite')), isNull);
      expect(InviteDeepLink.extractToken(Uri.parse('/invite')), isNull);
    });
  });

  group('InviteDeepLink.inviteLocationFromUri', () {
    test('returns invite page path for valid token', () {
      final uri = Uri.parse('vigia://invite/abc123');
      expect(InviteDeepLink.inviteLocationFromUri(uri), '/invite/abc123');
    });

    test('returns null when token cannot be extracted', () {
      final uri = Uri.parse('https://example.com/');
      expect(InviteDeepLink.inviteLocationFromUri(uri), isNull);
    });
  });
}
