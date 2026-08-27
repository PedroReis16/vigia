import { HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { DeviceShareInvite } from '@core/entities';
import { DeviceShareInviteMapper } from '@core/mappers';
import { DevicesService } from '@core/services';
import { firstValueFrom } from 'rxjs';
import { DevicesUseCaseError } from '../devices-use-case.error';

@Injectable({
  providedIn: 'root',
})
export class GenerateDeviceShareLinkService {
  private readonly devicesService = inject(DevicesService);

  async execute(deviceId: string): Promise<DeviceShareInvite> {
    try {
      const dto = await firstValueFrom(this.devicesService.generateShareLink(deviceId));
      return DeviceShareInviteMapper.fromDto(dto);
    } catch (error: unknown) {
      throw this.toDevicesError(error);
    }
  }

  private toDevicesError(error: unknown): DevicesUseCaseError {
    if (error instanceof HttpErrorResponse) {
      return new DevicesUseCaseError('DEVICES.ERRORS.SHARE', error.status);
    }
    return new DevicesUseCaseError('DEVICES.ERRORS.SHARE');
  }
}
