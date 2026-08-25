import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { vi } from 'vitest';
import { Device } from '@core/entities/classes/device';
import { DeviceRooms } from '@core/enums';
import { DeviceGroupsRealtimeService } from '@core/services';
import { GetDevicesService } from '@core/usecases';
import { VigiaTheme } from '@shared/theme/vigia.theme';
import { NEVER } from 'rxjs';
import { DevicesComponent } from './devices.component';

describe('DevicesComponent', () => {
  let fixture: ComponentFixture<DevicesComponent>;
  let getDevices: { execute: ReturnType<typeof vi.fn> };

  const sampleDevice = new Device(
    '1',
    'Vigia-a1b2c3d4',
    'Sala',
    'owner',
    'AA:BB',
    DeviceRooms.LivingRoom,
    null,
    true,
    false,
  );

  beforeEach(async () => {
    getDevices = {
      execute: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [DevicesComponent, TranslateModule.forRoot()],
      providers: [
        { provide: GetDevicesService, useValue: getDevices },
        {
          provide: DeviceGroupsRealtimeService,
          useValue: {
            membershipChanged$: NEVER,
            connect: vi.fn(),
            disconnect: vi.fn(),
          },
        },
        provideRouter([]),
        provideAnimationsAsync(),
        provideOptimus({
          theme: {
            preset: VigiaTheme,
            options: { darkModeSelector: '.vigia-dark' },
          },
        }),
      ],
    }).compileComponents();
  });

  async function createWithResult(result: Promise<Device[]>): Promise<void> {
    getDevices.execute.mockReturnValue(result);
    fixture = TestBed.createComponent(DevicesComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  }

  it('shows loading skeletons while fetching', async () => {
    let resolve!: (value: Device[]) => void;
    const pending = new Promise<Device[]>((res) => {
      resolve = res;
    });
    getDevices.execute.mockReturnValue(pending);

    fixture = TestBed.createComponent(DevicesComponent);
    fixture.detectChanges();

    expect(fixture.debugElement.query(By.css('[data-testid="devices-loading"]'))).toBeTruthy();

    resolve([]);
    await fixture.whenStable();
  });

  it('shows empty state when there are no devices', async () => {
    await createWithResult(Promise.resolve([]));
    expect(fixture.debugElement.query(By.css('[data-testid="devices-empty"]'))).toBeTruthy();
  });

  it('shows device cards when list is ready', async () => {
    await createWithResult(Promise.resolve([sampleDevice]));
    expect(fixture.debugElement.query(By.css('[data-testid="devices-list"]'))).toBeTruthy();
    expect(fixture.nativeElement.textContent).toContain('Sala');
  });

  it('shows error and retries through use case', async () => {
    getDevices.execute
      .mockRejectedValueOnce(new Error('fail'))
      .mockResolvedValueOnce([sampleDevice]);

    fixture = TestBed.createComponent(DevicesComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(fixture.debugElement.query(By.css('[data-testid="devices-error"]'))).toBeTruthy();

    const retry = fixture.debugElement.query(By.css('[data-testid="devices-retry"]'));
    retry.triggerEventHandler('onClick', {});
    await fixture.whenStable();
    fixture.detectChanges();

    expect(getDevices.execute).toHaveBeenCalledTimes(2);
    expect(fixture.debugElement.query(By.css('[data-testid="devices-list"]'))).toBeTruthy();
  });
});
