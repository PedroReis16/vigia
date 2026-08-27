import { inject, Injectable } from '@angular/core';
import { AuthSessionService } from '@core/services/auth/auth-session.service';
import { AuthHttpService } from '@core/services/http/auth/auth-http.service';
import { FirebaseMessagingService } from '@core/services/push/firebase-messaging.service';
import { NotificationStoreService } from '@core/services/notifications/notification-store.service';
import { UnregisterPushTokenService } from '@core/usecases/unregister-push-token/unregister-push-token.service';
import { firstValueFrom } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class LogoutService {
  private readonly authHttp = inject(AuthHttpService);
  private readonly session = inject(AuthSessionService);
  private readonly unregisterPushToken = inject(UnregisterPushTokenService);
  private readonly firebaseMessaging = inject(FirebaseMessagingService);
  private readonly notificationStore = inject(NotificationStoreService);

  async execute(): Promise<void> {
    const refreshToken = this.session.getRefreshToken();
    const pushToken = this.firebaseMessaging.getCurrentToken();

    await this.unregisterPushToken.execute(pushToken);
    this.firebaseMessaging.clearToken();
    this.notificationStore.clearForLogout();

    if (refreshToken) {
      try {
        await firstValueFrom(this.authHttp.logout({ refreshToken }));
      } catch {
        // Best-effort server revoke; local session is cleared regardless.
      }
    }

    this.session.clearSession();
  }
}
