import { TestBed } from '@angular/core/testing';
import { HttpErrorResponse } from '@angular/common/http';
import { vi } from 'vitest';
import { of, throwError } from 'rxjs';
import { DeviceClip } from '@core/entities';
import { ClipStatus } from '@core/enums';
import { DevicesService } from '@core/services';
import { DevicesUseCaseError } from '../devices-use-case.error';
import { GetDeviceClipsService } from './get-device-clips.service';

describe('GetDeviceClipsService', () => {
  let service: GetDeviceClipsService;
  let devicesService: { listClips: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    devicesService = { listClips: vi.fn() };
    TestBed.configureTestingModule({
      providers: [GetDeviceClipsService, { provide: DevicesService, useValue: devicesService }],
    });
    service = TestBed.inject(GetDeviceClipsService);
  });

  it('returns mapped clips', async () => {
    devicesService.listClips.mockReturnValue(
      of([
        {
          id: 'clip-1',
          deviceId: 'device-1',
          status: 'Assembling',
          frameCount: 60,
          fps: 30,
          createdAt: '2026-10-06T15:04:00Z',
        },
      ]),
    );

    const clips = await service.execute('device-1');
    expect(clips).toHaveLength(1);
    expect(clips[0]).toBeInstanceOf(DeviceClip);
    expect(clips[0].status).toBe(ClipStatus.Assembling);
    expect(clips[0].isPending).toBe(true);
  });

  it('maps not found', async () => {
    devicesService.listClips.mockReturnValue(
      throwError(() => new HttpErrorResponse({ status: 404 })),
    );

    await expect(service.execute('missing')).rejects.toEqual(
      expect.objectContaining({ message: 'DEVICES.ERRORS.NOT_FOUND', status: 404 }),
    );
  });

  it('maps other http errors', async () => {
    devicesService.listClips.mockReturnValue(
      throwError(() => new HttpErrorResponse({ status: 500 })),
    );

    await expect(service.execute('device-1')).rejects.toBeInstanceOf(DevicesUseCaseError);
    await expect(service.execute('device-1')).rejects.toEqual(
      expect.objectContaining({ message: 'DEVICES.ERRORS.CLIPS' }),
    );
  });
});
