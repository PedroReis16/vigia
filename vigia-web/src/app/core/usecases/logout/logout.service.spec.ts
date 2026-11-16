import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { AuthSessionService } from '@core/services/auth/auth-session.service';
import { KeycloakAuthService } from '@core/services/auth/keycloak-auth.service';
import { FirebaseMessagingService } from '@core/services/push/firebase-messaging.service';
import { NotificationStoreService } from '@core/services/notifications/notification-store.service';
import { UserProfileStoreService } from '@core/services/user-profile/user-profile-store.service';
import { LogoutSessionService } from '@core/usecases/logout-session/logout-session.service';
import { LogoutService } from './logout.service';

describe('LogoutService', () => {
  let service: LogoutService;
  let keycloak: {
    refreshToken: string | null;
    idToken: string | null;
    logout: ReturnType<typeof vi.fn>;
    clearToken: ReturnType<typeof vi.fn>;
  };
  let session: { clearSession: ReturnType<typeof vi.fn> };
  let logoutSession: { execute: ReturnType<typeof vi.fn> };
  let firebaseMessaging: {
    getCurrentToken: ReturnType<typeof vi.fn>;
    clearToken: ReturnType<typeof vi.fn>;
  };
  let notificationStore: { clearForLogout: ReturnType<typeof vi.fn> };
  let profileStore: { set: ReturnType<typeof vi.fn> };
  let assignMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    keycloak = {
      refreshToken: 'refresh-token',
      idToken: 'id-token',
      logout: vi.fn().mockResolvedValue(undefined),
      clearToken: vi.fn(),
    };
    session = { clearSession: vi.fn() };
    logoutSession = {
      execute: vi.fn().mockResolvedValue({ endSessionUrl: null }),
    };
    firebaseMessaging = {
      getCurrentToken: vi.fn(() => 'push-token'),
      clearToken: vi.fn(),
    };
    notificationStore = { clearForLogout: vi.fn() };
    profileStore = { set: vi.fn() };
    assignMock = vi.fn();
    vi.stubGlobal('location', {
      origin: 'http://localhost:4200',
      assign: assignMock,
    });

    TestBed.configureTestingModule({
      providers: [
        LogoutService,
        { provide: KeycloakAuthService, useValue: keycloak },
        { provide: AuthSessionService, useValue: session },
        { provide: LogoutSessionService, useValue: logoutSession },
        { provide: FirebaseMessagingService, useValue: firebaseMessaging },
        { provide: NotificationStoreService, useValue: notificationStore },
        { provide: UserProfileStoreService, useValue: profileStore },
      ],
    });
    service = TestBed.inject(LogoutService);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('calls API logout then Keycloak SSO when no endSessionUrl', async () => {
    await service.execute();

    expect(logoutSession.execute).toHaveBeenCalledWith({
      refreshToken: 'refresh-token',
      pushToken: 'push-token',
      idToken: 'id-token',
      postLogoutRedirectUri: 'http://localhost:4200/',
    });
    expect(firebaseMessaging.clearToken).toHaveBeenCalled();
    expect(notificationStore.clearForLogout).toHaveBeenCalled();
    expect(profileStore.set).toHaveBeenCalledWith(null);
    expect(keycloak.logout).toHaveBeenCalledWith('http://localhost:4200/');
    expect(assignMock).not.toHaveBeenCalled();
  });

  it('navigates to endSessionUrl when API returns one', async () => {
    logoutSession.execute.mockResolvedValue({
      endSessionUrl:
        'http://localhost/auth/realms/vigia/protocol/openid-connect/logout?x=1',
    });

    await service.execute();

    expect(keycloak.clearToken).toHaveBeenCalled();
    expect(session.clearSession).toHaveBeenCalled();
    expect(assignMock).toHaveBeenCalledWith(
      'http://localhost/auth/realms/vigia/protocol/openid-connect/logout?x=1',
    );
    expect(keycloak.logout).not.toHaveBeenCalled();
  });

  it('does not clear local push when API logout fails', async () => {
    logoutSession.execute.mockRejectedValue(new Error('keycloak refused'));

    await expect(service.execute()).rejects.toThrow('keycloak refused');

    expect(firebaseMessaging.clearToken).not.toHaveBeenCalled();
    expect(notificationStore.clearForLogout).not.toHaveBeenCalled();
    expect(profileStore.set).not.toHaveBeenCalled();
    expect(keycloak.logout).not.toHaveBeenCalled();
  });

  it('clears local session when there is no refresh token', async () => {
    keycloak.refreshToken = null;

    await service.execute();

    expect(logoutSession.execute).not.toHaveBeenCalled();
    expect(session.clearSession).toHaveBeenCalled();
    expect(keycloak.clearToken).toHaveBeenCalled();
  });
});
