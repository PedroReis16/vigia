import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';
import { vi } from 'vitest';
import { AuthSessionService } from '@core/services';
import { guestGuard } from './guest.guard';

describe('guestGuard', () => {
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

  it('allows anonymous users', () => {
    session.isAuthenticated.mockReturnValue(false);
    const result = TestBed.runInInjectionContext(() =>
      guestGuard({} as never, {} as never),
    );
    expect(result).toBe(true);
  });

  it('redirects authenticated users to devices', () => {
    session.isAuthenticated.mockReturnValue(true);
    TestBed.runInInjectionContext(() => guestGuard({} as never, {} as never));
    expect(router.createUrlTree).toHaveBeenCalledWith(['/devices']);
  });
});
