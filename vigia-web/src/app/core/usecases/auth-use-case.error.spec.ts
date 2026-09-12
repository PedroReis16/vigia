import { AuthErrorCode } from '@core/enums';
import { AuthUseCaseError } from './auth-use-case.error';

describe('AuthUseCaseError', () => {
  it('exposes message, code and optional status', () => {
    const error = new AuthUseCaseError('AUTH.ERRORS.LOGIN', AuthErrorCode.UnknownError, 500);
    expect(error.name).toBe('AuthUseCaseError');
    expect(error.message).toBe('AUTH.ERRORS.LOGIN');
    expect(error.code).toBe(AuthErrorCode.UnknownError);
    expect(error.status).toBe(500);
    expect(error).toBeInstanceOf(Error);
  });
});
