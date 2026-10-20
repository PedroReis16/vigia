import { inject, Injectable } from '@angular/core';
import { NotificationStoreService } from '@core/services/notifications/notification-store.service';
import { NotificationsHttpService } from '@core/services/http/notifications/notifications-http.service';
import { firstValueFrom } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class MarkNotificationReadService {
  private readonly http = inject(NotificationsHttpService);
  private readonly store = inject(NotificationStoreService);

  async execute(notificationId: string): Promise<void> {
    this.store.markRead(notificationId);
    try {
      await firstValueFrom(this.http.markRead(notificationId));
    } catch (error) {
      console.warn('[Vigia Notifications] Falha ao marcar notificação como lida.', error);
    }
  }
}
