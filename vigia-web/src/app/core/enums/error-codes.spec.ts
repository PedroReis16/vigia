import { AuthErrorCode, resolveAuthErrorCode } from './error-codes';

describe('resolveAuthErrorCode', () => {
  it('maps numeric email-in-use code', () => {
    expect(resolveAuthErrorCode(7)).toBe(AuthErrorCode.UserEmailAlreadyInUse);
  });

  it('maps string enum name case-insensitively', () => {
    expect(resolveAuthErrorCode('USER_EMAIL_ALREADY_IN_USE')).toBe(
      AuthErrorCode.UserEmailAlreadyInUse,
    );
    expect(resolveAuthErrorCode('user_email_already_in_use')).toBe(
      AuthErrorCode.UserEmailAlreadyInUse,
    );
  });

  it('falls back to unknown for null, undefined, or unrecognized values', () => {
    expect(resolveAuthErrorCode(null)).toBe(AuthErrorCode.UnknownError);
    expect(resolveAuthErrorCode(undefined)).toBe(AuthErrorCode.UnknownError);
    expect(resolveAuthErrorCode(99)).toBe(AuthErrorCode.UnknownError);
    expect(resolveAuthErrorCode('SOMETHING_ELSE')).toBe(AuthErrorCode.UnknownError);
    expect(resolveAuthErrorCode(0)).toBe(AuthErrorCode.UnknownError);
  });
});
