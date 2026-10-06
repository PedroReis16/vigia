import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { AuthSessionService } from './auth-session.service';
import { KeycloakAuthService } from './keycloak-auth.service';

describe('AuthSessionService', () => {
  let service: AuthSessionService;
  let keycloak: {
    authenticated: boolean;
    token: string | null;
    userId: string | null;
    updateToken: ReturnType<typeof vi.fn>;
    clearToken: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    keycloak = {
      authenticated: true,
      token: 'access',
      userId: 'user-1',
      updateToken: vi.fn().mockResolvedValue('access'),
      clearToken: vi.fn(),
    };

    TestBed.configureTestingModule({
      providers: [{ provide: KeycloakAuthService, useValue: keycloak }],
    });
    service = TestBed.inject(AuthSessionService);
  });

  it('reads the Keycloak session', () => {
    expect(service.isAuthenticated()).toBe(true);
    expect(service.getAccessToken()).toBe('access');
    expect(service.getUserId()).toBe('user-1');
  });

  it('refreshes and forces a new access token', async () => {
    await service.ensureFreshAccessToken();
    await service.forceRefreshAccessToken();

    expect(keycloak.updateToken).toHaveBeenNthCalledWith(1, 30);
    expect(keycloak.updateToken).toHaveBeenNthCalledWith(2, -1);
  });

  it('clears the Keycloak token', () => {
    service.clearSession();
    expect(keycloak.clearToken).toHaveBeenCalled();
  });
});
