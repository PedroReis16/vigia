import { AuthErrorCode } from '@core/enums';

export class AuthUseCaseError extends Error {
  constructor(
    message: string,
    public readonly code: AuthErrorCode,
    public readonly status?: number,
  ) {
    super(message);
    this.name = 'AuthUseCaseError';
  }
}
