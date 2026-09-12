import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';
import { vi } from 'vitest';
import { AuthSessionService, PendingInviteService } from '@core/services';
import { inviteEntryGuard } from './invite-entry.guard';

describe('inviteEntryGuard', () => {
  let session: { isAuthenticated: ReturnType<typeof vi.fn> };
  let pendingInvite: { setToken: ReturnType<typeof vi.fn> };
  let router: { createUrlTree: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    session = { isAuthenticated: vi.fn() };
    pendingInvite = { setToken: vi.fn() };
    router = { createUrlTree: vi.fn(() => ({}) as UrlTree) };

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthSessionService, useValue: session },
        { provide: PendingInviteService, useValue: pendingInvite },
        { provide: Router, useValue: router },
      ],
    });
  });

  it('allows authenticated users', () => {
    session.isAuthenticated.mockReturnValue(true);
    const result = TestBed.runInInjectionContext(() =>
      inviteEntryGuard(
        { paramMap: { get: () => 'token-1' } } as never,
        {} as never,
      ),
    );
    expect(result).toBe(true);
  });

  it('stores token and redirects anonymous users to login', () => {
    session.isAuthenticated.mockReturnValue(false);
    TestBed.runInInjectionContext(() =>
      inviteEntryGuard(
        { paramMap: { get: () => 'token-1' } } as never,
        {} as never,
      ),
    );
    expect(pendingInvite.setToken).toHaveBeenCalledWith('token-1');
    expect(router.createUrlTree).toHaveBeenCalledWith(['/login']);
  });

  it('redirects to devices when token is missing', () => {
    session.isAuthenticated.mockReturnValue(false);
    TestBed.runInInjectionContext(() =>
      inviteEntryGuard(
        { paramMap: { get: () => null } } as never,
        {} as never,
      ),
    );
    expect(router.createUrlTree).toHaveBeenCalledWith(['/devices']);
  });
});
