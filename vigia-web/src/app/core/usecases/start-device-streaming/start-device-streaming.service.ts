import { HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { DevicesService } from '@core/services';
import { firstValueFrom } from 'rxjs';
import { DevicesUseCaseError } from '../devices-use-case.error';

@Injectable({
  providedIn: 'root',
})
export class StartDeviceStreamingService {
  private readonly devicesService = inject(DevicesService);

  async execute(deviceId: string): Promise<void> {
    try {
      await firstValueFrom(this.devicesService.sendCommand(deviceId, 'START_STREAMING'));
    } catch (error: unknown) {
      throw this.toDevicesError(error);
    }
  }

  private toDevicesError(error: unknown): DevicesUseCaseError {
    if (error instanceof HttpErrorResponse) {
      return new DevicesUseCaseError('DEVICES.ERRORS.STREAM_COMMAND', error.status);
    }
    return new DevicesUseCaseError('DEVICES.ERRORS.STREAM_COMMAND');
  }
}
