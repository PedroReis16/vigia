import {
  HttpErrorResponse,
  HttpHandler,
  HttpHeaders,
  HttpRequest,
  HttpResponse,
} from '@angular/common/http';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { AuthSessionService } from '@core/services/auth/auth-session.service';
import { AuthInterceptor } from './auth.interceptor';

describe('AuthInterceptor', () => {
  let interceptor: AuthInterceptor;
  let session: {
    getAccessToken: ReturnType<typeof vi.fn>;
    getRefreshToken: ReturnType<typeof vi.fn>;
    setSession: ReturnType<typeof vi.fn>;
    clearSession: ReturnType<typeof vi.fn>;
  };
  let httpMock: HttpTestingController;

  beforeEach(() => {
    session = {
      getAccessToken: vi.fn(() => 'access'),
      getRefreshToken: vi.fn(() => 'refresh'),
      setSession: vi.fn(),
      clearSession: vi.fn(),
    };

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [AuthInterceptor, { provide: AuthSessionService, useValue: session }],
    });

    interceptor = TestBed.inject(AuthInterceptor);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('attaches bearer token', () => {
    const req = new HttpRequest('GET', '/devices');
    const next: HttpHandler = {
      handle: vi.fn(() => of(new HttpResponse({ status: 200, body: null }))),
    };

    interceptor.intercept(req, next).subscribe();

    const forwarded = (next.handle as ReturnType<typeof vi.fn>).mock
      .calls[0][0] as HttpRequest<unknown>;
    expect(forwarded.headers.get('Authorization')).toBe('Bearer access');
  });

  it('does not attach bearer when there is no access token', () => {
    session.getAccessToken.mockReturnValue(null);
    const req = new HttpRequest('GET', '/devices');
    const next: HttpHandler = {
      handle: vi.fn(() => of(new HttpResponse({ status: 200, body: null }))),
    };

    interceptor.intercept(req, next).subscribe();

    const forwarded = (next.handle as ReturnType<typeof vi.fn>).mock
      .calls[0][0] as HttpRequest<unknown>;
    expect(forwarded.headers.has('Authorization')).toBe(false);
  });

  it('skips auth header when Skip-Auth is set', () => {
    const req = new HttpRequest('POST', '/auth/login', {}, {
      headers: new HttpHeaders({ 'Skip-Auth': 'true' }),
    });
    const next: HttpHandler = {
      handle: vi.fn(() => of(new HttpResponse({ status: 200, body: null }))),
    };

    interceptor.intercept(req, next).subscribe();

    const forwarded = (next.handle as ReturnType<typeof vi.fn>).mock
      .calls[0][0] as HttpRequest<unknown>;
    expect(forwarded.headers.has('Skip-Auth')).toBe(false);
    expect(forwarded.headers.has('Authorization')).toBe(false);
  });

  it('refreshes token on 401 and retries', () => {
    const req = new HttpRequest('GET', '/devices');
    const next: HttpHandler = {
      handle: vi
        .fn()
        .mockReturnValueOnce(
          throwError(() => new HttpErrorResponse({ status: 401, url: '/devices' })),
        )
        .mockReturnValueOnce(of(new HttpResponse({ status: 200, body: { ok: true } }))),
    };

    let body: unknown;
    interceptor.intercept(req, next).subscribe((event) => {
      if (event instanceof HttpResponse) {
        body = event.body;
      }
    });

    const refresh = httpMock.expectOne((r) => r.url.includes('/auth/refresh'));
    refresh.flush({ accessToken: 'new-access', refreshToken: 'new-refresh' });

    expect(session.setSession).toHaveBeenCalledWith({
      accessToken: 'new-access',
      refreshToken: 'new-refresh',
    });
    expect(body).toEqual({ ok: true });
    expect(next.handle).toHaveBeenCalledTimes(2);
  });

  it('clears session when refresh fails', () => {
    const req = new HttpRequest('GET', '/devices');
    const next: HttpHandler = {
      handle: vi
        .fn()
        .mockReturnValue(
          throwError(() => new HttpErrorResponse({ status: 401, url: '/devices' })),
        ),
    };

    let failed = false;
    interceptor.intercept(req, next).subscribe({
      error: () => {
        failed = true;
      },
    });

    const refresh = httpMock.expectOne((r) => r.url.includes('/auth/refresh'));
    refresh.flush({ message: 'invalid' }, { status: 401, statusText: 'Unauthorized' });

    expect(session.clearSession).toHaveBeenCalled();
    expect(failed).toBe(true);
  });

  it('clears session on 401 when there is no refresh token', () => {
    session.getRefreshToken.mockReturnValue(null);
    const req = new HttpRequest('GET', '/devices');
    const next: HttpHandler = {
      handle: vi
        .fn()
        .mockReturnValue(
          throwError(() => new HttpErrorResponse({ status: 401, url: '/devices' })),
        ),
    };

    let failed = false;
    interceptor.intercept(req, next).subscribe({
      error: () => {
        failed = true;
      },
    });

    httpMock.expectNone((r) => r.url.includes('/auth/refresh'));
    expect(session.clearSession).toHaveBeenCalled();
    expect(failed).toBe(true);
  });

  it('does not attempt refresh for public auth paths', () => {
    const req = new HttpRequest('POST', 'http://localhost:81/vigia/auth/login', {});
    const next: HttpHandler = {
      handle: vi
        .fn()
        .mockReturnValue(
          throwError(
            () =>
              new HttpErrorResponse({
                status: 401,
                url: 'http://localhost:81/vigia/auth/login',
              }),
          ),
        ),
    };

    interceptor.intercept(req, next).subscribe({ error: () => undefined });

    httpMock.expectNone((r) => r.url.includes('/auth/refresh'));
    expect(session.clearSession).not.toHaveBeenCalled();
  });
});
