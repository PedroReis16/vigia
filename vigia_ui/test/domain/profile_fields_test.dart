import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_ui/domain/DTOs/user_profile.dart';
import 'package:vigia_ui/domain/profile_fields.dart';

void main() {
  test('accepts a trimmed name and rejects empty, long, or unsafe values', () {
    expect(isValidProfileName(' Ana '), isTrue);
    expect(isValidProfileName(' '), isFalse);
    expect(isValidProfileName('a' * 65), isFalse);
    expect(isValidProfileName('Ana<script>'), isFalse);
  });

  test('accepts a phone with 8 to 16 allowed characters', () {
    expect(isValidProfilePhone('11999990000'), isTrue);
    expect(isValidProfilePhone('+55 11 99999-0000'), isFalse);
    expect(isValidProfilePhone('1234567'), isFalse);
    expect(isValidProfilePhone('11 9999-0000'), isTrue);
  });

  test('reads whether the account can be deleted', () {
    final profile = UserProfile.fromJson({
      'id': 'user-1',
      'name': 'Ana',
      'canDeleteAccount': false,
    });

    expect(profile.canDeleteAccount, isFalse);
    expect(
      const UserProfile(
        id: 'user-2',
        name: 'Ana',
        firstName: 'Ana',
        lastName: 'Lima',
        email: 'ana@vigia.test',
        phone: '11999990000',
      ).canDeleteAccount,
      isTrue,
    );
  });
}
