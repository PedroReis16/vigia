import { HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Device } from '@core/entities/classes/device';
import { DeviceMapper } from '@core/mappers';
import { DevicesService } from '@core/services';
import { firstValueFrom } from 'rxjs';
import { DevicesUseCaseError } from '../devices-use-case.error';

@Injectable({
  providedIn: 'root',
})
export class GetDevicesService {
  private readonly devicesService = inject(DevicesService);

  async execute(): Promise<Device[]> {
    try {
      const dtos = await firstValueFrom(this.devicesService.getDevices());
      return DeviceMapper.fromDtoList(dtos);
    } catch (error: unknown) {
      throw this.toDevicesError(error);
    }
  }

  private toDevicesError(error: unknown): DevicesUseCaseError {
    if (error instanceof HttpErrorResponse) {
      return new DevicesUseCaseError('DEVICES.ERRORS.LIST', error.status);
    }

    return new DevicesUseCaseError('DEVICES.ERRORS.LIST');
  }
}