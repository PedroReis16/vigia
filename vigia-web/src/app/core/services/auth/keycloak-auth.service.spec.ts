import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { KeycloakAuthService } from './keycloak-auth.service';

const keycloakMock = vi.hoisted(() => ({
  init: vi.fn().mockResolvedValue(true),
  login: vi.fn().mockResolvedValue(undefined),
  register: vi.fn().mockResolvedValue(undefined),
  logout: vi.fn().mockResolvedValue(undefined),
  updateToken: vi.fn().mockResolvedValue(true),
  clearToken: vi.fn(),
}));

vi.mock('keycloak-js', () => ({
  default: class {
    authenticated = true;
    token = 'access';
    refreshToken = 'refresh';
    idToken = 'id-token';
    tokenParsed = { sub: 'user-1' };
    init = keycloakMock.init;
    login = keycloakMock.login;
    register = keycloakMock.register;
    logout = keycloakMock.logout;
    updateToken = keycloakMock.updateToken;
    clearToken = keycloakMock.clearToken;
  },
}));

function createStorage(): Storage {
  const values = new Map<string, string>();
  return {
    get length() {
      return values.size;
    },
    clear() {
      values.clear();
    },
    getItem(key: string) {
      return values.get(key) ?? null;
    },
    key(index: number) {
      return [...values.keys()][index] ?? null;
    },
    removeItem(key: string) {
      values.delete(key);
    },
    setItem(key: string, value: string) {
      values.set(key, value);
    },
  };
}

describe('KeycloakAuthService', () => {
  let service: KeycloakAuthService;

  beforeEach(() => {
    vi.stubGlobal('localStorage', createStorage());
    keycloakMock.init.mockReset();
    keycloakMock.init.mockResolvedValue(true);
    keycloakMock.login.mockClear();
    keycloakMock.register.mockClear();
    keycloakMock.logout.mockClear();
    keycloakMock.updateToken.mockClear();
    keycloakMock.clearToken.mockClear();
    keycloakMock.updateToken.mockResolvedValue(true);

    TestBed.configureTestingModule({});
    service = TestBed.inject(KeycloakAuthService);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('starts a PKCE check-sso session', async () => {
    await expect(service.init()).resolves.toBe(true);
    expect(keycloakMock.init).toHaveBeenCalledWith(
      expect.objectContaining({
        onLoad: 'check-sso',
        pkceMethod: 'S256',
        checkLoginIframe: false,
      }),
    );
    expect(service.authenticated).toBe(true);
    expect(service.token).toBe('access');
    expect(service.userId).toBe('user-1');
  });

  it('redirects to login, registration and logout', async () => {
    await service.login('http://localhost:4200/devices');
    await service.register('http://localhost:4200/devices');
    await service.logout('http://localhost:4200/');

    expect(keycloakMock.login).toHaveBeenCalledWith({
      redirectUri: 'http://localhost:4200/devices',
    });
    expect(keycloakMock.register).toHaveBeenCalledWith({
      redirectUri: 'http://localhost:4200/devices',
    });
    expect(keycloakMock.logout).toHaveBeenCalledWith({
      redirectUri: 'http://localhost:4200/',
    });
    expect(localStorage.getItem('vigia.auth.refreshToken')).toBeNull();
  });

  it('restores a stored session on the next load', async () => {
    localStorage.setItem('vigia.auth.accessToken', 'stored-access');
    localStorage.setItem('vigia.auth.refreshToken', 'stored-refresh');
    localStorage.setItem('vigia.auth.idToken', 'stored-id');

    await expect(service.init()).resolves.toBe(true);
    expect(keycloakMock.init).toHaveBeenCalledWith(
      expect.objectContaining({
        token: 'stored-access',
        refreshToken: 'stored-refresh',
        idToken: 'stored-id',
      }),
    );
  });

  it('keeps the session after a successful init', async () => {
    await service.init();

    expect(localStorage.getItem('vigia.auth.accessToken')).toBe('access');
    expect(localStorage.getItem('vigia.auth.refreshToken')).toBe('refresh');
    expect(localStorage.getItem('vigia.auth.idToken')).toBe('id-token');
  });

  it('drops a stored session that can no longer sign in', async () => {
    localStorage.setItem('vigia.auth.accessToken', 'stored-access');
    localStorage.setItem('vigia.auth.refreshToken', 'stored-refresh');
    keycloakMock.init.mockResolvedValueOnce(false);

    await expect(service.init()).resolves.toBe(false);
    expect(localStorage.getItem('vigia.auth.refreshToken')).toBeNull();
  });

  it('drops the stored session when the token is cleared', async () => {
    await service.init();
    service.clearToken();

    expect(localStorage.getItem('vigia.auth.accessToken')).toBeNull();
    expect(keycloakMock.clearToken).toHaveBeenCalled();
  });

  it('returns the refreshed access token', async () => {
    await service.init();
    await expect(service.updateToken(30)).resolves.toBe('access');
    expect(keycloakMock.updateToken).toHaveBeenCalledWith(30);
  });

  it('returns null when refresh fails', async () => {
    await service.init();
    keycloakMock.updateToken.mockRejectedValue(new Error('expired'));
    await expect(service.updateToken(-1)).resolves.toBeNull();
  });
});
