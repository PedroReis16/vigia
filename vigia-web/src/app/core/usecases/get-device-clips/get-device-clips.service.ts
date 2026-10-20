import { HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { DeviceClip } from '@core/entities';
import { DeviceClipMapper } from '@core/mappers';
import { DevicesService } from '@core/services';
import { firstValueFrom } from 'rxjs';
import { DevicesUseCaseError } from '../devices-use-case.error';

@Injectable({
  providedIn: 'root',
})
export class GetDeviceClipsService {
  private readonly devicesService = inject(DevicesService);

  async execute(deviceId: string): Promise<DeviceClip[]> {
    try {
      const dtos = await firstValueFrom(this.devicesService.listClips(deviceId));
      return DeviceClipMapper.fromDtoList(dtos);
    } catch (error: unknown) {
      throw this.toDevicesError(error);
    }
  }

  private toDevicesError(error: unknown): DevicesUseCaseError {
    if (error instanceof DevicesUseCaseError) {
      return error;
    }

    if (error instanceof HttpErrorResponse) {
      if (error.status === 404) {
        return new DevicesUseCaseError('DEVICES.ERRORS.NOT_FOUND', error.status);
      }
      return new DevicesUseCaseError('DEVICES.ERRORS.CLIPS', error.status);
    }

    return new DevicesUseCaseError('DEVICES.ERRORS.CLIPS');
  }
}
