import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { AuthSessionService } from '@core/services';
import { BeginKeycloakAuthService } from '@core/usecases';
import { authGuard } from './auth.guard';

describe('authGuard', () => {
  let session: { isAuthenticated: ReturnType<typeof vi.fn> };
  let beginAuth: { execute: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    session = { isAuthenticated: vi.fn() };
    beginAuth = { execute: vi.fn().mockResolvedValue(undefined) };

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthSessionService, useValue: session },
        { provide: BeginKeycloakAuthService, useValue: beginAuth },
      ],
    });
  });

  it('allows authenticated users', () => {
    session.isAuthenticated.mockReturnValue(true);
    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as never, { url: '/devices' } as never),
    );
    expect(result).toBe(true);
    expect(beginAuth.execute).not.toHaveBeenCalled();
  });

  it('starts Keycloak login for anonymous users', () => {
    session.isAuthenticated.mockReturnValue(false);
    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as never, { url: '/devices/abc' } as never),
    );
    expect(result).toBe(false);
    expect(beginAuth.execute).toHaveBeenCalledWith('login', '/devices/abc');
  });
});
