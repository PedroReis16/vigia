import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { AuthHttpService } from './auth-http.service';

describe('AuthHttpService', () => {
  let service: AuthHttpService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [AuthHttpService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AuthHttpService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('posts login with Skip-Auth header', () => {
    const body = { email: 'a@b.com', password: 'secret' };
    let response: unknown;

    service.login(body).subscribe((value) => {
      response = value;
    });

    const req = httpMock.expectOne('/auth/login');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(body);
    expect(req.request.headers.get('Skip-Auth')).toBe('true');
    req.flush({ accessToken: 'a', refreshToken: 'r' });

    expect(response).toEqual({ accessToken: 'a', refreshToken: 'r' });
  });

  it('posts register with Skip-Auth header', () => {
    const body = { name: 'Ana', email: 'a@b.com', password: 'password1' };

    service.register(body).subscribe();

    const req = httpMock.expectOne('/auth/register');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(body);
    expect(req.request.headers.get('Skip-Auth')).toBe('true');
    req.flush({ accessToken: 'a', refreshToken: 'r' }, { status: 201, statusText: 'Created' });
  });

  it('posts refresh with Skip-Auth header', () => {
    service.refresh({ refreshToken: 'old' }).subscribe();

    const req = httpMock.expectOne('/auth/refresh');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ refreshToken: 'old' });
    expect(req.request.headers.get('Skip-Auth')).toBe('true');
    req.flush({ accessToken: 'a2', refreshToken: 'r2' });
  });

  it('posts logout without Skip-Auth so bearer can be attached', () => {
    service.logout({ refreshToken: 'r' }).subscribe();

    const req = httpMock.expectOne('/auth/logout');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ refreshToken: 'r' });
    expect(req.request.headers.has('Skip-Auth')).toBe(false);
    req.flush(null, { status: 204, statusText: 'No Content' });
  });
});
