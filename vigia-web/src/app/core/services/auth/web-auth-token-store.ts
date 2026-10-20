const ACCESS_TOKEN_KEY = 'vigia.auth.accessToken';
const REFRESH_TOKEN_KEY = 'vigia.auth.refreshToken';
const ID_TOKEN_KEY = 'vigia.auth.idToken';

export interface StoredWebAuthTokens {
  token: string;
  refreshToken: string;
  idToken?: string;
}

/** Session kept across reloads so an invite link does not send an already signed-in user to Keycloak. */
export function readStoredWebAuthTokens(): StoredWebAuthTokens | null {
  try {
    const token = localStorage.getItem(ACCESS_TOKEN_KEY);
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!token || !refreshToken) {
      return null;
    }

    const idToken = localStorage.getItem(ID_TOKEN_KEY);
    return idToken ? { token, refreshToken, idToken } : { token, refreshToken };
  } catch {
    return null;
  }
}

export function writeStoredWebAuthTokens(tokens: StoredWebAuthTokens): void {
  try {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.token);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken);
    if (tokens.idToken) {
      localStorage.setItem(ID_TOKEN_KEY, tokens.idToken);
    } else {
      localStorage.removeItem(ID_TOKEN_KEY);
    }
  } catch {
    // Private mode still keeps the in-memory session for this page.
  }
}

export function clearStoredWebAuthTokens(): void {
  try {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(ID_TOKEN_KEY);
  } catch {
    // Nothing else to clear when storage is unavailable.
  }
}
