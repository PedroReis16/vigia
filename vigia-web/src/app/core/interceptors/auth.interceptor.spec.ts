import {
  HttpErrorResponse,
  HttpHandler,
  HttpHeaders,
  HttpRequest,
  HttpResponse,
} from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom, of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { AuthSessionService } from '@core/services/auth/auth-session.service';
import { AuthInterceptor } from './auth.interceptor';

describe('AuthInterceptor', () => {
  let interceptor: AuthInterceptor;
  let session: {
    getAccessToken: ReturnType<typeof vi.fn>;
    forceRefreshAccessToken: ReturnType<typeof vi.fn>;
    clearSession: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    session = {
      getAccessToken: vi.fn(() => 'access'),
      forceRefreshAccessToken: vi.fn().mockResolvedValue('new-access'),
      clearSession: vi.fn(),
    };

    TestBed.configureTestingModule({
      providers: [AuthInterceptor, { provide: AuthSessionService, useValue: session }],
    });

    interceptor = TestBed.inject(AuthInterceptor);
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
    const req = new HttpRequest('GET', '/devices', {
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

  it('refreshes the Keycloak token on 401 and retries', async () => {
    const req = new HttpRequest('GET', '/devices');
    const next: HttpHandler = {
      handle: vi
        .fn()
        .mockReturnValueOnce(
          throwError(() => new HttpErrorResponse({ status: 401, url: '/devices' })),
        )
        .mockReturnValueOnce(of(new HttpResponse({ status: 200, body: { ok: true } }))),
    };

    const event = await firstValueFrom(interceptor.intercept(req, next));

    expect(session.forceRefreshAccessToken).toHaveBeenCalled();
    expect(event).toBeInstanceOf(HttpResponse);
    expect((event as HttpResponse<{ ok: boolean }>).body).toEqual({ ok: true });
    const retry = (next.handle as ReturnType<typeof vi.fn>).mock.calls[1][0] as HttpRequest<unknown>;
    expect(retry.headers.get('Authorization')).toBe('Bearer new-access');
    expect(retry.headers.get('X-Auth-Retry')).toBe('true');
  });

  it('clears session when refresh returns no token', async () => {
    session.forceRefreshAccessToken.mockResolvedValue(null);
    const req = new HttpRequest('GET', '/devices');
    const next: HttpHandler = {
      handle: vi
        .fn()
        .mockReturnValue(
          throwError(() => new HttpErrorResponse({ status: 401, url: '/devices' })),
        ),
    };

    await expect(firstValueFrom(interceptor.intercept(req, next))).rejects.toBeTruthy();
    expect(session.clearSession).toHaveBeenCalled();
  });

  it('does not refresh twice for the same request', async () => {
    const req = new HttpRequest('GET', '/devices', {
      headers: new HttpHeaders({ 'X-Auth-Retry': 'true' }),
    });
    const next: HttpHandler = {
      handle: vi
        .fn()
        .mockReturnValue(
          throwError(() => new HttpErrorResponse({ status: 401, url: '/devices' })),
        ),
    };

    await expect(firstValueFrom(interceptor.intercept(req, next))).rejects.toBeTruthy();
    expect(session.forceRefreshAccessToken).not.toHaveBeenCalled();
    expect(session.clearSession).not.toHaveBeenCalled();
  });
});
