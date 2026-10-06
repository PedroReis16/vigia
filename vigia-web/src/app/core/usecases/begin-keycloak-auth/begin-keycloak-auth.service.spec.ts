import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { KeycloakAuthService } from '@core/services/auth/keycloak-auth.service';
import { BeginKeycloakAuthService } from './begin-keycloak-auth.service';

describe('BeginKeycloakAuthService', () => {
  let service: BeginKeycloakAuthService;
  let keycloak: {
    login: ReturnType<typeof vi.fn>;
    register: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    keycloak = {
      login: vi.fn().mockResolvedValue(undefined),
      register: vi.fn().mockResolvedValue(undefined),
    };

    TestBed.configureTestingModule({
      providers: [{ provide: KeycloakAuthService, useValue: keycloak }],
    });
    service = TestBed.inject(BeginKeycloakAuthService);
  });

  it('starts login with an absolute redirect', async () => {
    await service.execute('login', '/devices');

    expect(keycloak.login).toHaveBeenCalledWith(`${window.location.origin}/devices`);
    expect(keycloak.register).not.toHaveBeenCalled();
  });

  it('starts registration when mode is register', async () => {
    await service.execute('register', '/invite/token-1');

    expect(keycloak.register).toHaveBeenCalledWith(
      `${window.location.origin}/invite/token-1`,
    );
  });
});
