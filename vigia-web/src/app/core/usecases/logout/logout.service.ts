import { inject, Injectable } from '@angular/core';
import { AuthSessionService } from '@core/services/auth/auth-session.service';
import { KeycloakAuthService } from '@core/services/auth/keycloak-auth.service';
import { FirebaseMessagingService } from '@core/services/push/firebase-messaging.service';
import { NotificationStoreService } from '@core/services/notifications/notification-store.service';
import { LogoutSessionService } from '@core/usecases/logout-session/logout-session.service';

@Injectable({
  providedIn: 'root',
})
export class LogoutService {
  private readonly keycloak = inject(KeycloakAuthService);
  private readonly session = inject(AuthSessionService);
  private readonly logoutSession = inject(LogoutSessionService);
  private readonly firebaseMessaging = inject(FirebaseMessagingService);
  private readonly notificationStore = inject(NotificationStoreService);

  async execute(): Promise<void> {
    const refreshToken = this.keycloak.refreshToken;
    if (!refreshToken?.trim()) {
      this.session.clearSession();
      this.keycloak.clearToken();
      return;
    }

    const redirectUri =
      typeof window === 'undefined' ? undefined : `${window.location.origin}/`;
    const pushToken = this.firebaseMessaging.getCurrentToken();

    const result = await this.logoutSession.execute({
      refreshToken,
      pushToken,
      idToken: this.keycloak.idToken,
      postLogoutRedirectUri: redirectUri,
    });

    this.firebaseMessaging.clearToken();
    this.notificationStore.clearForLogout();

    if (result.endSessionUrl && typeof window !== 'undefined') {
      this.keycloak.clearToken();
      this.session.clearSession();
      window.location.assign(result.endSessionUrl);
      return;
    }

    try {
      await this.keycloak.logout(redirectUri);
    } catch {
      this.session.clearSession();
      this.keycloak.clearToken();
    }
  }
}
