import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';
import { vi } from 'vitest';
import { AuthSessionService } from '@core/services';
import { authGuard } from './auth.guard';

describe('authGuard', () => {
  let session: { isAuthenticated: ReturnType<typeof vi.fn> };
  let router: { createUrlTree: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    session = { isAuthenticated: vi.fn() };
    router = { createUrlTree: vi.fn(() => ({}) as UrlTree) };

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthSessionService, useValue: session },
        { provide: Router, useValue: router },
      ],
    });
  });

  it('allows authenticated users', () => {
    session.isAuthenticated.mockReturnValue(true);
    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as never, {} as never),
    );
    expect(result).toBe(true);
  });

  it('redirects anonymous users to login', () => {
    session.isAuthenticated.mockReturnValue(false);
    TestBed.runInInjectionContext(() => authGuard({} as never, {} as never));
    expect(router.createUrlTree).toHaveBeenCalledWith(['/login']);
  });
});
