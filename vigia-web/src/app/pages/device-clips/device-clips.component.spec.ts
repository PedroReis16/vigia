import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { ActivatedRoute } from '@angular/router';
import { vi } from 'vitest';
import { Device, DeviceClip } from '@core/entities';
import { ClipStatus, DeviceRooms } from '@core/enums';
import { GetDeviceClipsService, GetDeviceService } from '@core/usecases';
import { VigiaTheme } from '@shared/theme/vigia.theme';
import { DeviceClipsComponent } from './device-clips.component';

describe('DeviceClipsComponent', () => {
  let fixture: ComponentFixture<DeviceClipsComponent>;
  let getDevice: { execute: ReturnType<typeof vi.fn> };
  let getClips: { execute: ReturnType<typeof vi.fn> };

  const device = new Device(
    'device-1',
    'Vigia-test',
    'Sala',
    'owner',
    'AA:BB',
    DeviceRooms.LivingRoom,
    null,
    true,
    false,
    false,
  );

  const readyClip = new DeviceClip(
    'clip-ready',
    'device-1',
    ClipStatus.Ready,
    90,
    30,
    new Date('2026-10-06T15:04:00Z'),
    'https://example.test/thumb.jpg',
    'https://example.test/clip.mp4?accessToken=tok',
  );
  const pendingClip = new DeviceClip(
    'clip-pending',
    'device-1',
    ClipStatus.Receiving,
    30,
    30,
    new Date('2026-10-06T15:05:00Z'),
  );
  const legacyClip = new DeviceClip(
    'clip-legacy',
    'device-1',
    ClipStatus.Ready,
    60,
    30,
    new Date('2026-10-06T15:06:00Z'),
    null,
    'https://example.test/legacy.mp4?accessToken=tok',
  );

  beforeEach(async () => {
    getDevice = { execute: vi.fn().mockResolvedValue(device) };
    getClips = { execute: vi.fn().mockResolvedValue([]) };

    await TestBed.configureTestingModule({
      imports: [DeviceClipsComponent, TranslateModule.forRoot()],
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
        { provide: GetDeviceClipsService, useValue: getClips },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DeviceClipsComponent);
  });

  async function settle(): Promise<void> {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  }

  async function flush(): Promise<void> {
    fixture.detectChanges();
    await new Promise((resolve) => setTimeout(resolve, 0));
    fixture.detectChanges();
  }

  it('shows an empty list and the storage-off notice', async () => {
    await settle();

    expect(getClips.execute).toHaveBeenCalledWith('device-1');
    expect(fixture.nativeElement.querySelector('[data-testid="device-clips-empty"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('[data-testid="device-clips-disabled"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('[data-testid="device-clips-player"]')).toBeNull();
  });

  it('lists clips and plays only a ready clip', async () => {
    getClips.execute.mockResolvedValue([readyClip, pendingClip, legacyClip]);

    await flush();

    const ready = fixture.nativeElement.querySelector('[data-testid="device-clip-clip-ready"]');
    const pending = fixture.nativeElement.querySelector('[data-testid="device-clip-clip-pending"]');
    const legacy = fixture.nativeElement.querySelector('[data-testid="device-clip-clip-legacy"]');
    expect(ready.disabled).toBe(false);
    expect(pending.disabled).toBe(true);
    expect(ready.textContent).toContain('0:03');
    expect(ready.querySelector('[data-testid="device-clip-thumb-clip-ready"]')?.getAttribute('src')).toBe(
      'https://example.test/thumb.jpg',
    );
    expect(pending.querySelector('img')).toBeNull();
    expect(pending.querySelector('[data-testid="device-clip-thumb-fallback-clip-pending"]')).toBeTruthy();
    expect(legacy.querySelector('[data-testid="device-clip-thumb-fallback-clip-legacy"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('[data-testid="device-clips-player"]')).toBeNull();

    pending.click();
    await flush();
    expect(fixture.nativeElement.querySelector('[data-testid="device-clips-player"]')).toBeNull();

    ready.click();
    await flush();

    const player: HTMLVideoElement = fixture.nativeElement.querySelector(
      '[data-testid="device-clips-player"]',
    );
    expect(player).toBeTruthy();
    expect(player.getAttribute('src')).toBe('https://example.test/clip.mp4?accessToken=tok');
    expect(player.getAttribute('poster')).toBe('https://example.test/thumb.jpg');
    expect(fixture.nativeElement.querySelectorAll('[data-testid="device-clips-player"]')).toHaveLength(1);
  });

  it('shows an error state when the list fails', async () => {
    getClips.execute.mockRejectedValue(new Error('offline'));

    await settle();

    expect(fixture.nativeElement.querySelector('[data-testid="device-clips-error"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('[data-testid="device-clips-empty"]')).toBeNull();
  });

  it('refreshes while a clip is still being assembled', async () => {
    vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval'] });
    getClips.execute.mockResolvedValueOnce([pendingClip]).mockResolvedValue([readyClip]);

    await settle();
    expect(getClips.execute).toHaveBeenCalledTimes(1);

    await vi.advanceTimersByTimeAsync(5000);
    await fixture.whenStable();

    expect(getClips.execute).toHaveBeenCalledTimes(2);
    vi.useRealTimers();
  });
});
