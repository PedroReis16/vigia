import { HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Device } from '@core/entities';
import { DeviceMapper } from '@core/mappers';
import { DevicesService } from '@core/services';
import { firstValueFrom } from 'rxjs';
import { DevicesUseCaseError } from '../devices-use-case.error';

@Injectable({
  providedIn: 'root',
})
export class GetDeviceService {
  private readonly devicesService = inject(DevicesService);

  async execute(deviceId: string): Promise<Device> {
    try {
      const dto = await firstValueFrom(this.devicesService.getDevice(deviceId));
      if (!dto) {
        throw new DevicesUseCaseError('DEVICES.ERRORS.NOT_FOUND', 404);
      }
      return DeviceMapper.fromDto(dto);
    } catch (error: unknown) {
      if (error instanceof DevicesUseCaseError) {
        throw error;
      }
      throw this.toDevicesError(error);
    }
  }

  private toDevicesError(error: unknown): DevicesUseCaseError {
    if (error instanceof HttpErrorResponse) {
      if (error.status === 404 || error.status === 204) {
        return new DevicesUseCaseError('DEVICES.ERRORS.NOT_FOUND', error.status);
      }
      return new DevicesUseCaseError('DEVICES.ERRORS.DETAIL', error.status);
    }

    return new DevicesUseCaseError('DEVICES.ERRORS.DETAIL');
  }
}
