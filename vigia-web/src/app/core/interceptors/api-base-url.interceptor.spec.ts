import { HttpHandler, HttpRequest, HttpResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';
import { environment } from '@environments/environment';
import { ApiBaseUrlInterceptor } from './api-base-url.interceptor';

describe('ApiBaseUrlInterceptor', () => {
  let interceptor: ApiBaseUrlInterceptor;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ApiBaseUrlInterceptor],
    });
    interceptor = TestBed.inject(ApiBaseUrlInterceptor);
  });

  it('prefixes relative API paths with absolute apiUrl', () => {
    const req = new HttpRequest('GET', '/auth/login');
    const next: HttpHandler = {
      handle: vi.fn((r: HttpRequest<unknown>) => of(new HttpResponse({ body: null, url: r.url }))),
    };

    interceptor.intercept(req, next).subscribe();

    const forwarded = (next.handle as ReturnType<typeof vi.fn>).mock
      .calls[0][0] as HttpRequest<unknown>;
    expect(forwarded.url).toBe(`${environment.apiUrl.replace(/\/$/, '')}/auth/login`);
  });

  it('does not prefix absolute http URLs', () => {
    const req = new HttpRequest('GET', 'https://example.com/x');
    const next: HttpHandler = {
      handle: vi.fn((r: HttpRequest<unknown>) => of(new HttpResponse({ body: null, url: r.url }))),
    };

    interceptor.intercept(req, next).subscribe();
    expect(next.handle).toHaveBeenCalledWith(req);
  });

  it('does not prefix relative asset paths like i18n', () => {
    const req = new HttpRequest('GET', './i18n/pt-BR.json');
    const next: HttpHandler = {
      handle: vi.fn((r: HttpRequest<unknown>) => of(new HttpResponse({ body: null, url: r.url }))),
    };

    interceptor.intercept(req, next).subscribe();
    expect(next.handle).toHaveBeenCalledWith(req);
  });
});
