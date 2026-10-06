import { inject, Injectable } from '@angular/core';
import { AuthSessionService } from '@core/services/auth/auth-session.service';
import { KeycloakAuthService } from '@core/services/auth/keycloak-auth.service';
import { FirebaseMessagingService } from '@core/services/push/firebase-messaging.service';
import { NotificationStoreService } from '@core/services/notifications/notification-store.service';
import { UnregisterPushTokenService } from '@core/usecases/unregister-push-token/unregister-push-token.service';

@Injectable({
  providedIn: 'root',
})
export class LogoutService {
  private readonly keycloak = inject(KeycloakAuthService);
  private readonly session = inject(AuthSessionService);
  private readonly unregisterPushToken = inject(UnregisterPushTokenService);
  private readonly firebaseMessaging = inject(FirebaseMessagingService);
  private readonly notificationStore = inject(NotificationStoreService);

  async execute(): Promise<void> {
    const pushToken = this.firebaseMessaging.getCurrentToken();

    await this.unregisterPushToken.execute(pushToken);
    this.firebaseMessaging.clearToken();
    this.notificationStore.clearForLogout();

    const redirectUri =
      typeof window === 'undefined' ? undefined : `${window.location.origin}/`;

    try {
      await this.keycloak.logout(redirectUri);
    } catch {
      this.session.clearSession();
    }
  }
}
