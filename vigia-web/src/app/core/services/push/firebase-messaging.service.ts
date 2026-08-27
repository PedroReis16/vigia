import { Injectable, OnDestroy } from '@angular/core';
import {
  describePushInitFailure,
  isFirebaseConfigured,
  PushInitFailureReason,
  toFirebaseAppOptions,
} from '@core/interfaces/firebase-config';
import { environment } from '@environments/environment';
import { Subject } from 'rxjs';

export interface IncomingFallAlertMessage {
  payload: Record<string, string>;
  notification?: {
    title?: string;
    body?: string;
  };
}

type FirebaseMessagingModule = typeof import('firebase/messaging');
type FirebaseAppModule = typeof import('firebase/app');

@Injectable({
  providedIn: 'root',
})
export class FirebaseMessagingService implements OnDestroy {
  private app: import('firebase/app').FirebaseApp | null = null;
  private messaging: import('firebase/messaging').Messaging | null = null;
  private firebaseAppModule: FirebaseAppModule | null = null;
  private firebaseMessagingModule: FirebaseMessagingModule | null = null;
  private serviceWorkerRegistration: ServiceWorkerRegistration | null = null;
  private currentToken: string | null = null;
  private foregroundUnsubscribe: (() => void) | null = null;
  private serviceWorkerListener: ((event: MessageEvent) => void) | null = null;
  private messagingPrepared = false;

  private readonly messageSubject = new Subject<IncomingFallAlertMessage>();
  readonly messages$ = this.messageSubject.asObservable();

  ngOnDestroy(): void {
    this.teardown();
    this.messageSubject.complete();
  }

  getCurrentToken(): string | null {
    return this.currentToken;
  }

  getNotificationPermission(): NotificationPermission {
    if (typeof Notification === 'undefined') {
      return 'denied';
    }

    return Notification.permission;
  }

  /** Sets up Firebase, service worker and foreground listeners (no permission prompt). */
  async prepareMessaging(): Promise<boolean> {
    if (this.messagingPrepared) {
      return true;
    }

    const failure = await this.getInitFailureReason();
    if (failure) {
      console.warn(`[Vigia Push] ${describePushInitFailure(failure)}`);
      return false;
    }

    const [appModule, messagingModule] = await Promise.all([
      import('firebase/app'),
      import('firebase/messaging'),
    ]);
    this.firebaseAppModule = appModule;
    this.firebaseMessagingModule = messagingModule;

    this.app =
      appModule.getApps().length > 0
        ? appModule.getApp()
        : appModule.initializeApp(toFirebaseAppOptions(environment.firebase));
    this.messaging = messagingModule.getMessaging(this.app);

    await navigator.serviceWorker.register('/firebase-messaging-sw.js');
    this.serviceWorkerRegistration = await navigator.serviceWorker.ready;

    this.attachServiceWorkerListener();

    this.foregroundUnsubscribe = messagingModule.onMessage(this.messaging, (message) => {
      this.messageSubject.next({
        payload: this.normalizeData(message.data),
        notification: {
          title: message.notification?.title,
          body: message.notification?.body,
        },
      });
    });

    this.messagingPrepared = true;
    return true;
  }

  /** Requests permission (when needed) and returns the FCM token. Call from a user gesture when possible. */
  async acquireToken(): Promise<string | null> {
    if (!(await this.prepareMessaging())) {
      return null;
    }

    const messaging = this.messaging;
    const messagingModule = this.firebaseMessagingModule;
    const registration = this.serviceWorkerRegistration;
    if (!messaging || !messagingModule || !registration) {
      return null;
    }

    let permission = this.getNotificationPermission();
    if (permission === 'default') {
      permission = await Notification.requestPermission();
    }

    if (permission !== 'granted') {
      console.warn(`[Vigia Push] ${describePushInitFailure('permission_denied')}`);
      return null;
    }

    try {
      this.currentToken = await messagingModule.getToken(messaging, {
        vapidKey: environment.firebase.vapidKey,
        serviceWorkerRegistration: registration,
      });
    } catch (error) {
      console.warn(`[Vigia Push] ${describePushInitFailure('token_error')}`, error);
      return null;
    }

    if (this.currentToken) {
      console.info('[Vigia Push] Token FCM web obtido.');
    }

    return this.currentToken;
  }

  private async getInitFailureReason(): Promise<PushInitFailureReason | null> {
    if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
      return 'unsupported';
    }

    if (!isFirebaseConfigured(environment.firebase)) {
      return 'not_configured';
    }

    try {
      const messagingModule = await import('firebase/messaging');
      const supported = await messagingModule.isSupported();
      return supported ? null : 'unsupported';
    } catch {
      return 'unsupported';
    }
  }

  clearToken(): void {
    this.currentToken = null;
  }

  private attachServiceWorkerListener(): void {
    if (typeof navigator === 'undefined' || !navigator.serviceWorker || this.serviceWorkerListener) {
      return;
    }

    this.serviceWorkerListener = (event: MessageEvent) => {
      const data = event.data as
        | {
            type?: string;
            payload?: Record<string, string>;
            notification?: { title?: string; body?: string };
            deviceId?: string;
          }
        | undefined;

      if (!data?.type) {
        return;
      }

      if (data.type === 'FALL_ALERT' && data.payload) {
        this.messageSubject.next({
          payload: this.normalizeData(data.payload),
          notification: data.notification,
        });
        return;
      }

      if (data.type === 'NOTIFICATION_CLICK' && data.deviceId) {
        this.messageSubject.next({
          payload: {
            type: 'fall',
            deviceId: data.deviceId,
          },
        });
      }
    };

    navigator.serviceWorker.addEventListener('message', this.serviceWorkerListener);
  }

  private normalizeData(data: unknown): Record<string, string> {
    if (!data || typeof data !== 'object') {
      return {};
    }

    return Object.fromEntries(
      Object.entries(data as Record<string, unknown>)
        .filter(([, value]) => value != null)
        .map(([key, value]) => [key, String(value)]),
    );
  }

  private teardown(): void {
    this.foregroundUnsubscribe?.();
    this.foregroundUnsubscribe = null;

    if (this.serviceWorkerListener && typeof navigator !== 'undefined') {
      navigator.serviceWorker.removeEventListener('message', this.serviceWorkerListener);
    }
    this.serviceWorkerListener = null;
    this.messagingPrepared = false;
  }
}
