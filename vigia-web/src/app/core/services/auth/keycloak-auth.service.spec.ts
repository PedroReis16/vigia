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
    tokenParsed = { sub: 'user-1' };
    init = keycloakMock.init;
    login = keycloakMock.login;
    register = keycloakMock.register;
    logout = keycloakMock.logout;
    updateToken = keycloakMock.updateToken;
    clearToken = keycloakMock.clearToken;
  },
}));

describe('KeycloakAuthService', () => {
  let service: KeycloakAuthService;

  beforeEach(() => {
    keycloakMock.init.mockClear();
    keycloakMock.login.mockClear();
    keycloakMock.register.mockClear();
    keycloakMock.logout.mockClear();
    keycloakMock.updateToken.mockClear();
    keycloakMock.clearToken.mockClear();
    keycloakMock.updateToken.mockResolvedValue(true);

    TestBed.configureTestingModule({});
    service = TestBed.inject(KeycloakAuthService);
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
