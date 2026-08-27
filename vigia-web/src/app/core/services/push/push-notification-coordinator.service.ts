import { DestroyRef, inject, Injectable } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { parseFallAlertPayload } from '@core/helpers/fall-alert-payload.helper';
import { NotificationStoreService } from '@core/services/notifications/notification-store.service';
import {
  FirebaseMessagingService,
  IncomingFallAlertMessage,
} from '@core/services/push/firebase-messaging.service';
import { NavigateToFallAlertService } from '@core/usecases/navigate-to-fall-alert/navigate-to-fall-alert.service';
import { RegisterPushTokenService } from '@core/usecases/register-push-token/register-push-token.service';

@Injectable({
  providedIn: 'root',
})
export class PushNotificationCoordinatorService {
  private readonly destroyRef = inject(DestroyRef);
  private readonly firebaseMessaging = inject(FirebaseMessagingService);
  private readonly notificationStore = inject(NotificationStoreService);
  private readonly registerPushToken = inject(RegisterPushTokenService);
  private readonly navigateToFallAlert = inject(NavigateToFallAlertService);

  private listenersReady = false;

  initialize(): void {
    this.ensureListeners();

    if (this.firebaseMessaging.getNotificationPermission() === 'granted') {
      void this.syncPushToken();
    }
  }

  async syncPushToken(): Promise<boolean> {
    this.ensureListeners();

    const token = await this.firebaseMessaging.acquireToken();
    if (!token) {
      return false;
    }

    try {
      await this.registerPushToken.execute(token);
      console.info('[Vigia Push] Token registrado na API.');
      return true;
    } catch (error) {
      console.warn('[Vigia Push] Falha ao registrar token na API.', error);
      return false;
    }
  }

  private ensureListeners(): void {
    if (this.listenersReady) {
      return;
    }
    this.listenersReady = true;

    this.notificationStore.bindToCurrentUser();

    void this.firebaseMessaging.prepareMessaging();

    this.firebaseMessaging.messages$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((message) => {
        void this.handleIncomingMessage(message);
      });
  }

  private async handleIncomingMessage(message: IncomingFallAlertMessage): Promise<void> {
    const isNotificationClick =
      message.payload['type'] === 'fall' &&
      Boolean(message.payload['deviceId']) &&
      !message.notification &&
      !message.payload['deviceName'];

    if (isNotificationClick) {
      await this.navigateToFallAlert.execute(message.payload);
      return;
    }

    const notification = parseFallAlertPayload(message.payload, message.notification);
    if (!notification) {
      return;
    }

    this.notificationStore.add(notification);
    this.showForegroundSystemNotification(notification.title, notification.body);
  }

  private showForegroundSystemNotification(title: string, body: string): void {
    if (typeof Notification === 'undefined' || Notification.permission !== 'granted') {
      return;
    }

    try {
      new Notification(title, {
        body,
        icon: '/images/vigia-logo.png',
      });
    } catch {
      // Ignore browsers that block programmatic notifications.
    }
  }
}
