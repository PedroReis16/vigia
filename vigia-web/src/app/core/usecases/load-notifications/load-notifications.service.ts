import { inject, Injectable } from '@angular/core';
import { mapUserNotificationDto } from '@core/helpers/fall-alert-payload.helper';
import { NotificationStoreService } from '@core/services/notifications/notification-store.service';
import { NotificationsHttpService } from '@core/services/http/notifications/notifications-http.service';
import { firstValueFrom } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class LoadNotificationsService {
  private readonly http = inject(NotificationsHttpService);
  private readonly store = inject(NotificationStoreService);

  async execute(): Promise<void> {
    const result = await firstValueFrom(this.http.list());
    this.store.replaceAll(
      (result.items ?? []).map(mapUserNotificationDto),
      result.unreadCount ?? 0,
    );
  }
}
