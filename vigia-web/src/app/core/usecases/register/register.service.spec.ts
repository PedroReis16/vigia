import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { AuthErrorCode } from '@core/enums';
import { AuthHttpService } from '@core/services/http/auth/auth-http.service';
import { AuthSessionService } from '@core/services/auth/auth-session.service';
import { RegisterService } from './register.service';

describe('RegisterService', () => {
  let service: RegisterService;
  let authHttp: { register: ReturnType<typeof vi.fn> };
  let session: { setSession: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    authHttp = { register: vi.fn() };
    session = { setSession: vi.fn() };

    TestBed.configureTestingModule({
      providers: [
        RegisterService,
        { provide: AuthHttpService, useValue: authHttp },
        { provide: AuthSessionService, useValue: session },
      ],
    });
    service = TestBed.inject(RegisterService);
  });

  it('stores session on success', async () => {
    const tokens = { accessToken: 'a', refreshToken: 'r' };
    authHttp.register.mockReturnValue(of(tokens));

    await service.execute({ name: 'Ana', email: 'a@b.com', password: 'password1' });

    expect(authHttp.register).toHaveBeenCalledWith({
      name: 'Ana',
      email: 'a@b.com',
      password: 'password1',
    });
    expect(session.setSession).toHaveBeenCalledWith(tokens);
  });

  it('maps email already in use from string errorCode', async () => {
    authHttp.register.mockReturnValue(
      throwError(
        () =>
          new HttpErrorResponse({
            status: 400,
            error: { errorCode: 'USER_EMAIL_ALREADY_IN_USE' },
          }),
      ),
    );

    await expect(
      service.execute({ name: 'Ana', email: 'a@b.com', password: 'password1' }),
    ).rejects.toMatchObject({
      message: 'AUTH.ERRORS.EMAIL_IN_USE',
      code: AuthErrorCode.UserEmailAlreadyInUse,
      status: 400,
    });
  });

  it('maps email already in use from numeric errorCode', async () => {
    authHttp.register.mockReturnValue(
      throwError(
        () =>
          new HttpErrorResponse({
            status: 400,
            error: { errorCode: 7 },
          }),
      ),
    );

    await expect(
      service.execute({ name: 'Ana', email: 'a@b.com', password: 'password1' }),
    ).rejects.toMatchObject({
      message: 'AUTH.ERRORS.EMAIL_IN_USE',
      code: AuthErrorCode.UserEmailAlreadyInUse,
    });
  });

  it('maps other HTTP errors to generic register message', async () => {
    authHttp.register.mockReturnValue(
      throwError(() => new HttpErrorResponse({ status: 500, error: {} })),
    );

    await expect(
      service.execute({ name: 'Ana', email: 'a@b.com', password: 'password1' }),
    ).rejects.toMatchObject({
      message: 'AUTH.ERRORS.REGISTER',
      code: AuthErrorCode.UnknownError,
    });
  });

  it('maps non-HTTP failures to generic register message', async () => {
    authHttp.register.mockReturnValue(throwError(() => new Error('offline')));

    await expect(
      service.execute({ name: 'Ana', email: 'a@b.com', password: 'password1' }),
    ).rejects.toMatchObject({
      message: 'AUTH.ERRORS.REGISTER',
    });
    expect(session.setSession).not.toHaveBeenCalled();
  });
});
