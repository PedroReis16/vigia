import { inject, Injectable } from '@angular/core';
import { PushNotificationCoordinatorService } from '@core/services/push/push-notification-coordinator.service';

@Injectable({
  providedIn: 'root',
})
export class SyncPushNotificationsService {
  private readonly coordinator = inject(PushNotificationCoordinatorService);

  async execute(): Promise<boolean> {
    return this.coordinator.syncPushToken();
  }
}
