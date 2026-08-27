import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { ActivatedRoute } from '@angular/router';
import { vi } from 'vitest';
import { Device } from '@core/entities';
import { DeviceRooms } from '@core/enums';
import { DeviceGroupsRealtimeService, WhepLiveSession, AuthSessionService, DeviceDetailTransitionService } from '@core/services';
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

  it('shows mobile app bar with device nickname and status', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const appBar = fixture.nativeElement.querySelector('[data-testid="device-detail-appbar"]');
    expect(appBar).toBeTruthy();
    expect(appBar.textContent).toContain('Sala');

    const status = fixture.nativeElement.querySelector('[data-testid="device-detail-appbar-status"]');
    expect(status).toBeTruthy();
    expect(status.textContent).toContain('ONLINE');
  });

  it('shows status badge in details panel on all viewports', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const badge = fixture.nativeElement.querySelector('[data-testid="device-status-badge"]');
    expect(badge).toBeTruthy();
    expect(badge.textContent).toContain('ONLINE');
    expect(badge.querySelector('.device-details-panel__status-dot--online')).toBeTruthy();
  });

  it('renders two-column layout container for responsive desktop', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const layout = fixture.nativeElement.querySelector('[data-testid="device-detail-layout"]');
    expect(layout).toBeTruthy();
    expect(layout.querySelector('.device-detail__player-wrap')).toBeTruthy();
    expect(layout.querySelector('.device-detail__panel')).toBeTruthy();
  });

  it('renders desktop clips action row in the video column', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const clips = fixture.nativeElement.querySelector('[data-testid="device-detail-clips"]');
    expect(clips).toBeTruthy();
    expect(clips.querySelector('[data-testid="device-clips-desktop-action"]')).toBeTruthy();
  });

  it('collapses video when virtual keyboard opens', async () => {
    const visualViewport = {
      height: 400,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };

    Object.defineProperty(window, 'visualViewport', {
      configurable: true,
      value: visualViewport,
    });
    Object.defineProperty(window, 'innerHeight', {
      configurable: true,
      value: 800,
    });

    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const resizeHandler = visualViewport.addEventListener.mock.calls.find(
      ([event]) => event === 'resize',
    )?.[1] as () => void;

    expect(resizeHandler).toBeDefined();

    resizeHandler();
    fixture.detectChanges();

    const video = fixture.nativeElement.querySelector('.device-detail__video');
    expect(video.classList.contains('device-detail__video--collapsed')).toBe(true);
  });

  it('hides the video slot while enter transition is pending', async () => {
    const transition = TestBed.inject(DeviceDetailTransitionService);
    transition.armEnter({
      deviceId: 'device-1',
      displayName: 'Sala',
      thumbnailUrl: null,
      imageFailed: false,
      bounds: { top: 0, left: 0, width: 120, height: 80 },
      borderRadius: 12,
    });

    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const page = fixture.nativeElement.querySelector('[data-testid="device-detail-page"]');
    const videoInner = fixture.nativeElement.querySelector('[data-testid="device-detail-video-target"]');

    expect(page.classList.contains('device-detail--enter-pending')).toBe(true);
    expect(getComputedStyle(videoInner).opacity).toContain('clamp');

    const appBar = fixture.nativeElement.querySelector('[data-testid="device-detail-appbar"]');
    expect(appBar).toBeTruthy();
    expect(appBar.classList.contains('device-detail__transition-reveal')).toBe(true);
    expect(getComputedStyle(appBar).clipPath).toContain('ellipse');
    expect(fixture.componentInstance.revealProgress()).toBe(0);
  });

  it('mounts live player while enter transition is still pending', async () => {
    const transition = TestBed.inject(DeviceDetailTransitionService);
    transition.armEnter({
      deviceId: 'device-1',
      displayName: 'Sala',
      thumbnailUrl: null,
      imageFailed: false,
      bounds: { top: 0, left: 0, width: 120, height: 80 },
      borderRadius: 12,
    });

    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('app-device-video-player')).toBeTruthy();
    expect(transition.settled()).toBe(false);
  });

  it('notifies transition ready after view init when enter is armed', async () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { pathname: '/devices/device-1' },
    });

    const shell = document.createElement('div');
    shell.dataset['testid'] = 'device-detail-video-target';
    const player = document.createElement('div');
    player.className = 'device-video-player';
    Object.defineProperty(player, 'getBoundingClientRect', {
      value: () => ({
        top: 56,
        left: 0,
        width: 390,
        height: 219,
        right: 390,
        bottom: 275,
        x: 0,
        y: 56,
        toJSON: () => ({}),
      }),
    });
    Object.defineProperty(shell, 'getBoundingClientRect', {
      value: () => ({
        top: 56,
        left: 0,
        width: 390,
        height: 219,
        right: 390,
        bottom: 275,
        x: 0,
        y: 56,
        toJSON: () => ({}),
      }),
    });
    shell.appendChild(player);
    document.body.appendChild(shell);

    const transition = TestBed.inject(DeviceDetailTransitionService);
    const notifySpy = vi.spyOn(transition, 'notifyReady');

    transition.armEnter({
      deviceId: 'device-1',
      displayName: 'Sala',
      thumbnailUrl: null,
      imageFailed: false,
      bounds: { top: 0, left: 0, width: 120, height: 80 },
      borderRadius: 12,
    });

    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: () => ({
        matches: false,
        media: '',
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }),
    });

    fixture.detectChanges();
    await fixture.whenStable();
    await new Promise((resolve) => setTimeout(resolve, 0));
    await fixture.whenStable();

    expect(notifySpy).toHaveBeenCalled();
  });
});
