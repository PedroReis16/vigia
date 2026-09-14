import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { DeviceRooms } from '@core/enums';
import { DevicesService } from '@core/services';
import { DevicesUseCaseError } from '../devices-use-case.error';
import { GetDevicesService } from './get-devices.service';

describe('GetDevicesService', () => {
  let service: GetDevicesService;
  let devicesHttp: { getDevices: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    devicesHttp = {
      getDevices: vi.fn(),
    };

    TestBed.configureTestingModule({
      providers: [
        GetDevicesService,
        { provide: DevicesService, useValue: devicesHttp },
      ],
    });

    service = TestBed.inject(GetDevicesService);
  });

  it('maps devices from HTTP service', async () => {
    devicesHttp.getDevices.mockReturnValue(
      of([
        {
          id: '1',
          name: 'Vigia-a1b2c3d4',
          nickname: 'Sala',
          room: DeviceRooms.LivingRoom,
          macAddress: 'AA:BB',
          thumbnailUrl: null,
          isRunning: true,
          isClipsEnabled: false,
        },
      ]),
    );

    const devices = await service.execute();

    expect(devices).toHaveLength(1);
    expect(devices[0].displayName).toBe('Sala');
    expect(devices[0].isRunning).toBe(true);
  });

  it('throws DevicesUseCaseError when HTTP fails', async () => {
    devicesHttp.getDevices.mockReturnValue(
      throwError(
        () =>
          new HttpErrorResponse({
            status: 500,
            statusText: 'Server Error',
          }),
      ),
    );

    await expect(service.execute()).rejects.toBeInstanceOf(DevicesUseCaseError);
    await expect(service.execute()).rejects.toMatchObject({
      message: 'DEVICES.ERRORS.LIST',
      status: 500,
    });
  });
});
