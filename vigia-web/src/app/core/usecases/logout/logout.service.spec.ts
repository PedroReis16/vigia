import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { AuthHttpService } from '@core/services/http/auth/auth-http.service';
import { AuthSessionService } from '@core/services/auth/auth-session.service';
import { FirebaseMessagingService } from '@core/services/push/firebase-messaging.service';
import { NotificationStoreService } from '@core/services/notifications/notification-store.service';
import { UnregisterPushTokenService } from '@core/usecases/unregister-push-token/unregister-push-token.service';
import { LogoutService } from './logout.service';

describe('LogoutService', () => {
  let service: LogoutService;
  let authHttp: { logout: ReturnType<typeof vi.fn> };
  let session: {
    getRefreshToken: ReturnType<typeof vi.fn>;
    clearSession: ReturnType<typeof vi.fn>;
  };
  let unregisterPushToken: { execute: ReturnType<typeof vi.fn> };
  let firebaseMessaging: {
    getCurrentToken: ReturnType<typeof vi.fn>;
    clearToken: ReturnType<typeof vi.fn>;
  };
  let notificationStore: { clearForLogout: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    authHttp = { logout: vi.fn() };
    session = {
      getRefreshToken: vi.fn(() => 'refresh'),
      clearSession: vi.fn(),
    };
    unregisterPushToken = { execute: vi.fn().mockResolvedValue(undefined) };
    firebaseMessaging = {
      getCurrentToken: vi.fn(() => 'push-token'),
      clearToken: vi.fn(),
    };
    notificationStore = { clearForLogout: vi.fn() };

    TestBed.configureTestingModule({
      providers: [
        LogoutService,
        { provide: AuthHttpService, useValue: authHttp },
        { provide: AuthSessionService, useValue: session },
        { provide: UnregisterPushTokenService, useValue: unregisterPushToken },
        { provide: FirebaseMessagingService, useValue: firebaseMessaging },
        { provide: NotificationStoreService, useValue: notificationStore },
      ],
    });
    service = TestBed.inject(LogoutService);
  });

  it('clears session even when logout request fails', async () => {
    authHttp.logout.mockReturnValue(throwError(() => new Error('network')));

    await service.execute();

    expect(unregisterPushToken.execute).toHaveBeenCalledWith('push-token');
    expect(firebaseMessaging.clearToken).toHaveBeenCalled();
    expect(notificationStore.clearForLogout).toHaveBeenCalled();
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
