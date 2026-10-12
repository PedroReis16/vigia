import { inject, Injectable } from '@angular/core';
import { NotificationStoreService } from '@core/services/notifications/notification-store.service';
import { NotificationsHttpService } from '@core/services/http/notifications/notifications-http.service';
import { firstValueFrom } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class MarkAllNotificationsReadService {
  private readonly http = inject(NotificationsHttpService);
  private readonly store = inject(NotificationStoreService);

  async execute(): Promise<void> {
    this.store.markAllRead();
    try {
      await firstValueFrom(this.http.markAllRead());
    } catch (error) {
      console.warn('[Vigia Notifications] Falha ao marcar todas como lidas.', error);
    }
  }
}
