import { TestBed } from '@angular/core/testing';
import { HttpErrorResponse } from '@angular/common/http';
import { vi } from 'vitest';
import { of, throwError } from 'rxjs';
import { Device } from '@core/entities';
import { DeviceRooms } from '@core/enums';
import { DevicesService } from '@core/services';
import { DevicesUseCaseError } from '../devices-use-case.error';
import { GetDeviceService } from './get-device.service';

describe('GetDeviceService', () => {
  let service: GetDeviceService;
  let devicesService: { getDevice: ReturnType<typeof vi.fn> };

  const dto = {
    id: '1',
    name: 'Vigia-test',
    nickname: 'Sala',
    room: DeviceRooms.LivingRoom,
    ownerId: 'owner',
    macAddress: 'AA:BB',
    thumbnailUrl: null,
    isRunning: true,
    isClipsEnabled: false,
  };

  beforeEach(() => {
    devicesService = { getDevice: vi.fn() };
    TestBed.configureTestingModule({
      providers: [GetDeviceService, { provide: DevicesService, useValue: devicesService }],
    });
    service = TestBed.inject(GetDeviceService);
  });

  it('returns mapped device', async () => {
    devicesService.getDevice.mockReturnValue(of(dto));

    const device = await service.execute('1');
    expect(device).toBeInstanceOf(Device);
    expect(device.displayName).toBe('Sala');
  });

  it('throws not found when dto is null', async () => {
    devicesService.getDevice.mockReturnValue(of(null));

    await expect(service.execute('missing')).rejects.toEqual(
      expect.objectContaining({ message: 'DEVICES.ERRORS.NOT_FOUND' }),
    );
  });

  it('maps http errors', async () => {
    devicesService.getDevice.mockReturnValue(
      throwError(() => new HttpErrorResponse({ status: 500 })),
    );

    await expect(service.execute('1')).rejects.toBeInstanceOf(DevicesUseCaseError);
  });
});
