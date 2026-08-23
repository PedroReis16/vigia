import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { AuthHttpService } from '@core/services/http/auth/auth-http.service';
import { AuthSessionService } from '@core/services/auth/auth-session.service';
import { LogoutService } from './logout.service';

describe('LogoutService', () => {
  let service: LogoutService;
  let authHttp: { logout: ReturnType<typeof vi.fn> };
  let session: {
    getRefreshToken: ReturnType<typeof vi.fn>;
    clearSession: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    authHttp = { logout: vi.fn() };
    session = {
      getRefreshToken: vi.fn(() => 'refresh'),
      clearSession: vi.fn(),
    };

    TestBed.configureTestingModule({
      providers: [
        LogoutService,
        { provide: AuthHttpService, useValue: authHttp },
        { provide: AuthSessionService, useValue: session },
      ],
    });
    service = TestBed.inject(LogoutService);
  });

  it('clears session even when logout request fails', async () => {
    authHttp.logout.mockReturnValue(throwError(() => new Error('network')));

    await service.execute();

    expect(authHttp.logout).toHaveBeenCalledWith({ refreshToken: 'refresh' });
    expect(session.clearSession).toHaveBeenCalled();
  });

  it('clears session when there is no refresh token', async () => {
    session.getRefreshToken.mockReturnValue(null);

    await service.execute();

    expect(authHttp.logout).not.toHaveBeenCalled();
    expect(session.clearSession).toHaveBeenCalled();
  });

  it('calls logout then clears session on success', async () => {
    authHttp.logout.mockReturnValue(of(undefined));

    await service.execute();

    expect(authHttp.logout).toHaveBeenCalled();
    expect(session.clearSession).toHaveBeenCalled();
  });
});
