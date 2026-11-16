import { inject, Injectable } from '@angular/core';
import { DevicesService } from '@core/services/http/devices/devices.service';
import { LoadNotificationsService } from '@core/usecases/load-notifications/load-notifications.service';
import { firstValueFrom } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class AcknowledgeDeviceAlertsService {
  private readonly devices = inject(DevicesService);
  private readonly loadNotifications = inject(LoadNotificationsService);

  async execute(deviceId: string): Promise<void> {
    try {
      await firstValueFrom(this.devices.acknowledgeAlerts(deviceId));
      await this.loadNotifications.execute();
    } catch (error) {
      console.warn('[Vigia Notifications] Falha ao confirmar alerta do device.', error);
    }
  }
}
