import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { AuthSessionService } from '@core/services/auth/auth-session.service';
import { KeycloakAuthService } from '@core/services/auth/keycloak-auth.service';
import { FirebaseMessagingService } from '@core/services/push/firebase-messaging.service';
import { NotificationStoreService } from '@core/services/notifications/notification-store.service';
import { UnregisterPushTokenService } from '@core/usecases/unregister-push-token/unregister-push-token.service';
import { LogoutService } from './logout.service';

describe('LogoutService', () => {
  let service: LogoutService;
  let keycloak: { logout: ReturnType<typeof vi.fn> };
  let session: { clearSession: ReturnType<typeof vi.fn> };
  let unregisterPushToken: { execute: ReturnType<typeof vi.fn> };
  let firebaseMessaging: {
    getCurrentToken: ReturnType<typeof vi.fn>;
    clearToken: ReturnType<typeof vi.fn>;
  };
  let notificationStore: { clearForLogout: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    keycloak = { logout: vi.fn().mockResolvedValue(undefined) };
    session = { clearSession: vi.fn() };
    unregisterPushToken = { execute: vi.fn().mockResolvedValue(undefined) };
    firebaseMessaging = {
      getCurrentToken: vi.fn(() => 'push-token'),
      clearToken: vi.fn(),
    };
    notificationStore = { clearForLogout: vi.fn() };

    TestBed.configureTestingModule({
      providers: [
        LogoutService,
        { provide: KeycloakAuthService, useValue: keycloak },
        { provide: AuthSessionService, useValue: session },
        { provide: UnregisterPushTokenService, useValue: unregisterPushToken },
        { provide: FirebaseMessagingService, useValue: firebaseMessaging },
        { provide: NotificationStoreService, useValue: notificationStore },
      ],
    });
    service = TestBed.inject(LogoutService);
  });

  it('unregisters push and ends the Keycloak session', async () => {
    await service.execute();

    expect(unregisterPushToken.execute).toHaveBeenCalledWith('push-token');
    expect(firebaseMessaging.clearToken).toHaveBeenCalled();
    expect(notificationStore.clearForLogout).toHaveBeenCalled();
    expect(keycloak.logout).toHaveBeenCalledWith(`${window.location.origin}/`);
    expect(session.clearSession).not.toHaveBeenCalled();
  });

  it('clears the local session when Keycloak logout fails', async () => {
    keycloak.logout.mockRejectedValue(new Error('network'));

    await service.execute();

    expect(session.clearSession).toHaveBeenCalled();
  });
});
