import { computed, Injectable, signal } from '@angular/core';
import { FallNotification } from '@core/entities/classes/fall-notification';

@Injectable({
  providedIn: 'root',
})
export class NotificationStoreService {
  private readonly notificationsState = signal<FallNotification[]>([]);
  private readonly unreadCountState = signal(0);

  readonly notifications = this.notificationsState.asReadonly();
  readonly unreadCount = computed(() => this.unreadCountState());

  bindToCurrentUser(): void {
    // Inbox is loaded from the API via LoadNotificationsService.
  }

  clearForLogout(): void {
    this.notificationsState.set([]);
    this.unreadCountState.set(0);
  }

  replaceAll(notifications: FallNotification[], unreadCount: number): void {
    this.notificationsState.set(notifications);
    this.unreadCountState.set(unreadCount);
  }

  upsert(notification: FallNotification): void {
    const existing = this.notificationsState();
    const withoutDupes = existing.filter(
      (item) =>
        item.id !== notification.id &&
        !(notification.episodeId && item.episodeId === notification.episodeId),
    );
    const next = [notification, ...withoutDupes].sort((left, right) =>
      right.receivedAt.localeCompare(left.receivedAt),
    );
    this.notificationsState.set(next);
    this.unreadCountState.set(next.filter((item) => !item.read).length);
  }

  markRead(id: string): void {
    const next = this.notificationsState().map((notification) =>
      notification.id === id ? { ...notification, read: true } : notification,
    );
    this.notificationsState.set(next);
    this.unreadCountState.set(next.filter((item) => !item.read).length);
  }

  markAllRead(): void {
    const next = this.notificationsState().map((notification) => ({
      ...notification,
      read: true,
    }));
    this.notificationsState.set(next);
    this.unreadCountState.set(0);
  }
}
