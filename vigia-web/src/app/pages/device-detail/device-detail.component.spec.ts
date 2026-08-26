import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { ActivatedRoute } from '@angular/router';
import { vi } from 'vitest';
import { Device } from '@core/entities';
import { DeviceRooms } from '@core/enums';
import { DeviceGroupsRealtimeService, WhepLiveSession, AuthSessionService } from '@core/services';
import {
  GetDeviceService,
  GetDeviceUsersService,
  StartDeviceStreamingService,
} from '@core/usecases';
import { VigiaTheme } from '@shared/theme/vigia.theme';
import { NEVER } from 'rxjs';
import { DeviceDetailComponent } from './device-detail.component';

describe('DeviceDetailComponent', () => {
  let fixture: ComponentFixture<DeviceDetailComponent>;
  let getDevice: { execute: ReturnType<typeof vi.fn> };
  let getDeviceUsers: { execute: ReturnType<typeof vi.fn> };
  let startStreaming: { execute: ReturnType<typeof vi.fn> };

  const sampleDevice = new Device(
    'device-1',
    'Vigia-test',
    'Sala',
    'owner',
    'AA:BB',
    DeviceRooms.LivingRoom,
    null,
    true,
    false,
  );

  beforeEach(async () => {
    vi.spyOn(WhepLiveSession.prototype, 'connect').mockResolvedValue(undefined);
    vi.spyOn(WhepLiveSession.prototype, 'close').mockResolvedValue(undefined);

    getDevice = { execute: vi.fn().mockResolvedValue(sampleDevice) };
    getDeviceUsers = { execute: vi.fn().mockResolvedValue([]) };
    startStreaming = { execute: vi.fn().mockResolvedValue(undefined) };

    await TestBed.configureTestingModule({
      imports: [DeviceDetailComponent, TranslateModule.forRoot()],
      providers: [
        provideRouter([]),
        provideAnimationsAsync(),
        provideOptimus({
          theme: {
            preset: VigiaTheme,
            options: { darkModeSelector: false },
          },
        }),
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: { get: () => 'device-1' } } },
        },
        { provide: GetDeviceService, useValue: getDevice },
        { provide: GetDeviceUsersService, useValue: getDeviceUsers },
        { provide: StartDeviceStreamingService, useValue: startStreaming },
        {
          provide: DeviceGroupsRealtimeService,
          useValue: { membershipChanged$: NEVER, connect: vi.fn(), disconnect: vi.fn() },
        },
        {
          provide: AuthSessionService,
          useValue: { getUserId: () => 'owner' },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DeviceDetailComponent);
  });

  it('loads device and shows detail page', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(getDevice.execute).toHaveBeenCalledWith('device-1');
    expect(fixture.debugElement.nativeElement.textContent).toContain('Sala');
  });
});
