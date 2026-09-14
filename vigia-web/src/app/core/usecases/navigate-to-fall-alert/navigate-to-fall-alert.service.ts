import { inject, Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { FallAlertPayload } from '@core/entities/classes/fall-notification';
import { resolveFallAlertDeviceId } from '@core/helpers/fall-alert-payload.helper';

@Injectable({
  providedIn: 'root',
})
export class NavigateToFallAlertService {
  private readonly router = inject(Router);

  async execute(data: FallAlertPayload): Promise<boolean> {
    const deviceId = resolveFallAlertDeviceId(data);
    if (!deviceId) {
      return false;
    }

    await this.router.navigate(['/devices', deviceId]);
    return true;
  }
}
