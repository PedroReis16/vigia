import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { AuthErrorCode } from '@core/enums';
import { AuthHttpService } from '@core/services/http/auth/auth-http.service';
import { AuthSessionService } from '@core/services/auth/auth-session.service';
import { LoginService } from './login.service';

describe('LoginService', () => {
  let service: LoginService;
  let authHttp: { login: ReturnType<typeof vi.fn> };
  let session: { setSession: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    authHttp = { login: vi.fn() };
    session = { setSession: vi.fn() };

    TestBed.configureTestingModule({
      providers: [
        LoginService,
        { provide: AuthHttpService, useValue: authHttp },
        { provide: AuthSessionService, useValue: session },
      ],
    });
    service = TestBed.inject(LoginService);
  });

  it('stores session on success', async () => {
    const tokens = { accessToken: 'a', refreshToken: 'r' };
    authHttp.login.mockReturnValue(of(tokens));

    await service.execute({ email: 'a@b.com', password: 'secret' });

    expect(authHttp.login).toHaveBeenCalledWith({ email: 'a@b.com', password: 'secret' });
    expect(session.setSession).toHaveBeenCalledWith(tokens);
  });

  it('maps 401 to invalid credentials', async () => {
    authHttp.login.mockReturnValue(
      throwError(() => new HttpErrorResponse({ status: 401 })),
    );

    await expect(service.execute({ email: 'a@b.com', password: 'x' })).rejects.toMatchObject({
      message: 'AUTH.ERRORS.INVALID_CREDENTIALS',
      status: 401,
    });
    expect(session.setSession).not.toHaveBeenCalled();
  });

  it('maps other HTTP errors to generic login message', async () => {
    authHttp.login.mockReturnValue(
      throwError(
        () =>
          new HttpErrorResponse({
            status: 500,
            error: { errorCode: 'UNKNOWN_ERROR' },
          }),
      ),
    );

    await expect(service.execute({ email: 'a@b.com', password: 'x' })).rejects.toMatchObject({
      message: 'AUTH.ERRORS.LOGIN',
      code: AuthErrorCode.UnknownError,
      status: 500,
    });
  });

  it('maps non-HTTP failures to generic login message', async () => {
    authHttp.login.mockReturnValue(throwError(() => new Error('network')));

    await expect(service.execute({ email: 'a@b.com', password: 'x' })).rejects.toMatchObject({
      message: 'AUTH.ERRORS.LOGIN',
      code: AuthErrorCode.UnknownError,
    });
  });
});
