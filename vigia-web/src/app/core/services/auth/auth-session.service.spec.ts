import { TestBed } from '@angular/core/testing';
import { AUTH_STORAGE_KEYS } from '@core/constants';
import { AuthSessionService } from './auth-session.service';
import { StorageService } from '../storage/storage.service';

describe('AuthSessionService', () => {
  let service: AuthSessionService;
  let storage: Record<string, string>;

  beforeEach(() => {
    storage = {};
    TestBed.configureTestingModule({
      providers: [
        AuthSessionService,
        {
          provide: StorageService,
          useValue: {
            getItem: (key: string) => storage[key] ?? null,
            setItem: (key: string, value: string) => {
              storage[key] = value;
            },
            removeItem: (key: string) => {
              delete storage[key];
            },
          },
        },
      ],
    });
    service = TestBed.inject(AuthSessionService);
  });

  it('is authenticated when refresh token exists', () => {
    expect(service.isAuthenticated()).toBe(false);
    const accessToken = [
      btoa(JSON.stringify({ alg: 'none' })),
      btoa(JSON.stringify({ sub: 'user-1' })),
      '',
    ].join('.');
    
    service.setSession({
      accessToken: accessToken, //gitleaks:allow
      refreshToken: 'refresh',
    });
    expect(service.isAuthenticated()).toBe(true);
    expect(service.getAccessToken()).toBe(accessToken);
    expect(service.getRefreshToken()).toBe('refresh');
    expect(service.getUserId()).toBe('user-1');
  });

  it('stores tokens without user id when JWT has no sub', () => {
    service.setSession({
      accessToken: `h.${btoa(JSON.stringify({ email: 'a@b.com' }))}.s`,
      refreshToken: 'r',
    });
    expect(service.getUserId()).toBeNull();
    expect(storage[AUTH_STORAGE_KEYS.userId]).toBeUndefined();
  });

  it('treats empty refresh token as unauthenticated', () => {
    storage[AUTH_STORAGE_KEYS.refreshToken] = '';
    expect(service.isAuthenticated()).toBe(false);
  });

  it('clears all session keys', () => {
    service.setSession({ accessToken: 'a.b.c', refreshToken: 'r' });
    service.clearSession();
    expect(service.getAccessToken()).toBeNull();
    expect(service.getRefreshToken()).toBeNull();
    expect(service.getUserId()).toBeNull();
    expect(storage[AUTH_STORAGE_KEYS.accessToken]).toBeUndefined();
    expect(storage[AUTH_STORAGE_KEYS.refreshToken]).toBeUndefined();
    expect(storage[AUTH_STORAGE_KEYS.userId]).toBeUndefined();
  });
});
