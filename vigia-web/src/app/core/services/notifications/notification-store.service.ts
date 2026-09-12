import { computed, inject, Injectable, signal } from '@angular/core';
import { FallNotification } from '@core/entities/classes/fall-notification';
import { AuthSessionService } from '@core/services/auth/auth-session.service';

const MAX_NOTIFICATIONS = 50;
const STORAGE_PREFIX = 'vigia:notifications:';

@Injectable({
  providedIn: 'root',
})
export class NotificationStoreService {
  private readonly session = inject(AuthSessionService);

  private readonly notificationsState = signal<FallNotification[]>([]);
  private storageKey: string | null = null;

  readonly notifications = this.notificationsState.asReadonly();
  readonly unreadCount = computed(
    () => this.notificationsState().filter((notification) => !notification.read).length,
  );

  bindToCurrentUser(): void {
    const userId = this.session.getUserId();
    this.storageKey = userId ? `${STORAGE_PREFIX}${userId}` : null;
    this.notificationsState.set(this.loadFromStorage());
  }

  clearForLogout(): void {
    this.storageKey = null;
    this.notificationsState.set([]);
  }

  add(notification: FallNotification): void {
    const next = [notification, ...this.notificationsState()]
      .slice(0, MAX_NOTIFICATIONS)
      .sort((left, right) => right.receivedAt.localeCompare(left.receivedAt));

    this.notificationsState.set(next);
    this.persist();
  }

  markRead(id: string): void {
    const next = this.notificationsState().map((notification) =>
      notification.id === id ? { ...notification, read: true } : notification,
    );
    this.notificationsState.set(next);
    this.persist();
  }

  markAllRead(): void {
    const next = this.notificationsState().map((notification) => ({
      ...notification,
      read: true,
    }));
    this.notificationsState.set(next);
    this.persist();
  }

  private loadFromStorage(): FallNotification[] {
    if (!this.storageKey || typeof localStorage === 'undefined') {
      return [];
    }

    try {
      const raw = localStorage.getItem(this.storageKey);
      if (!raw) {
        return [];
      }

      const parsed = JSON.parse(raw) as FallNotification[];
      if (!Array.isArray(parsed)) {
        return [];
      }

      return parsed
        .filter((item) => item?.type === 'fall' && typeof item.deviceId === 'string')
        .slice(0, MAX_NOTIFICATIONS);
    } catch {
      return [];
    }
  }

  private persist(): void {
    if (!this.storageKey || typeof localStorage === 'undefined') {
      return;
    }

    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.notificationsState()));
    } catch {
      // Ignore quota or privacy mode errors.
    }
  }
}
