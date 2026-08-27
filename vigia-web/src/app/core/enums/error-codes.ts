export enum AuthErrorCode {
  UnknownError = 'UNKNOWN_ERROR',
  UserEmailAlreadyInUse = 'USER_EMAIL_ALREADY_IN_USE',
}

/** Numeric values kept for compatibility with older clients. */
export const AUTH_ERROR_CODE_VALUES: Record<number, AuthErrorCode> = {
  0: AuthErrorCode.UnknownError,
  7: AuthErrorCode.UserEmailAlreadyInUse,
};

export function resolveAuthErrorCode(raw: string | number | undefined | null): AuthErrorCode {
  if (raw === undefined || raw === null) {
    return AuthErrorCode.UnknownError;
  }

  if (typeof raw === 'number') {
    return AUTH_ERROR_CODE_VALUES[raw] ?? AuthErrorCode.UnknownError;
  }

  const normalized = raw.toUpperCase();
  if (normalized === AuthErrorCode.UserEmailAlreadyInUse) {
    return AuthErrorCode.UserEmailAlreadyInUse;
  }

  return AuthErrorCode.UnknownError;
}
