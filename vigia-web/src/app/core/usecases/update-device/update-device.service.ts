import { HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Device, UpdateDeviceDto } from '@core/entities';
import { DeviceRooms } from '@core/enums';
import { DeviceMapper } from '@core/mappers';
import { DevicesService } from '@core/services';
import { firstValueFrom } from 'rxjs';
import { DevicesUseCaseError } from '../devices-use-case.error';
import { GetDeviceService } from '../get-device/get-device.service';

export interface UpdateDeviceInput {
  nickname?: string | null;
  room?: DeviceRooms | null;
  isClipsEnabled?: boolean | null;
}

@Injectable({
  providedIn: 'root',
})
export class UpdateDeviceService {
  private readonly devicesService = inject(DevicesService);
  private readonly getDevice = inject(GetDeviceService);

  async execute(deviceId: string, input: UpdateDeviceInput): Promise<Device> {
    const body: UpdateDeviceDto = {
      nickname: input.nickname,
      room: input.room,
      isClipsEnabled: input.isClipsEnabled,
    };

    try {
      await firstValueFrom(this.devicesService.updateDevice(deviceId, body));
      return this.getDevice.execute(deviceId);
    } catch (error: unknown) {
      throw this.toDevicesError(error);
    }
  }

  private toDevicesError(error: unknown): DevicesUseCaseError {
    if (error instanceof DevicesUseCaseError) {
      return error;
    }
    if (error instanceof HttpErrorResponse) {
      return new DevicesUseCaseError('DEVICES.ERRORS.UPDATE', error.status);
    }
    return new DevicesUseCaseError('DEVICES.ERRORS.UPDATE');
  }
}
