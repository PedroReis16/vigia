import { HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { DevicesService } from '@core/services';
import { firstValueFrom } from 'rxjs';
import { DevicesUseCaseError } from '../devices-use-case.error';

@Injectable({
  providedIn: 'root',
})
export class RemoveDeviceUserService {
  private readonly devicesService = inject(DevicesService);

  async execute(deviceId: string, userId: string): Promise<void> {
    try {
      await firstValueFrom(this.devicesService.removeDeviceUser(deviceId, userId));
    } catch (error: unknown) {
      throw this.toDevicesError(error);
    }
  }

  private toDevicesError(error: unknown): DevicesUseCaseError {
    if (error instanceof HttpErrorResponse) {
      return new DevicesUseCaseError('DEVICES.ERRORS.REMOVE_USER', error.status);
    }
    return new DevicesUseCaseError('DEVICES.ERRORS.REMOVE_USER');
  }
}
