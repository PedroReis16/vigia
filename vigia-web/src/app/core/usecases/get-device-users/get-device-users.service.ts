import { HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { DeviceUser } from '@core/entities';
import { DeviceUserMapper } from '@core/mappers';
import { DevicesService } from '@core/services';
import { firstValueFrom } from 'rxjs';
import { DevicesUseCaseError } from '../devices-use-case.error';

@Injectable({
  providedIn: 'root',
})
export class GetDeviceUsersService {
  private readonly devicesService = inject(DevicesService);

  async execute(deviceId: string): Promise<DeviceUser[]> {
    try {
      const dtos = await firstValueFrom(this.devicesService.getDeviceUsers(deviceId));
      return DeviceUserMapper.fromDtoList(dtos);
    } catch (error: unknown) {
      throw this.toDevicesError(error);
    }
  }

  private toDevicesError(error: unknown): DevicesUseCaseError {
    if (error instanceof HttpErrorResponse) {
      return new DevicesUseCaseError('DEVICES.ERRORS.USERS', error.status);
    }
    return new DevicesUseCaseError('DEVICES.ERRORS.USERS');
  }
}
