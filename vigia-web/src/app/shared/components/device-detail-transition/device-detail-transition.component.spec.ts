import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DeviceDetailTransitionService } from '@core/services';
import { DeviceDetailTransitionComponent } from './device-detail-transition.component';

function mockRect(
  element: HTMLElement,
  rect: { top: number; left: number; width: number; height: number },
): void {
  Object.defineProperty(element, 'getBoundingClientRect', {
    value: () => ({
      ...rect,
      right: rect.left + rect.width,
      bottom: rect.top + rect.height,
      x: rect.left,
      y: rect.top,
      toJSON: () => ({}),
    }),
  });
}

describe('DeviceDetailTransitionComponent', () => {
  let fixture: ComponentFixture<DeviceDetailTransitionComponent>;
  let transition: DeviceDetailTransitionService;

  beforeEach(async () => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: (query: string) => ({
        matches: query.includes('prefers-reduced-motion'),
        media: query,
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
      }),
    });

    await TestBed.configureTestingModule({
      imports: [DeviceDetailTransitionComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(DeviceDetailTransitionComponent);
    transition = TestBed.inject(DeviceDetailTransitionService);
    fixture.detectChanges();
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('completes immediately when reduced motion is preferred', () => {
    transition.armEnter({
      deviceId: 'device-1',
      displayName: 'Sala',
      thumbnailUrl: null,
      imageFailed: false,
      bounds: { top: 0, left: 0, width: 120, height: 80 },
      borderRadius: 12,
    });
    transition.notifyReady();

    fixture.detectChanges();

    expect(transition.settled()).toBe(true);
    expect(transition.kind()).toBe('idle');
  });

  it('starts enter overlay immediately when ready', () => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: () => ({
        matches: false,
        media: '',
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
      }),
    });

    const shell = document.createElement('div');
    shell.dataset['testid'] = 'device-detail-video-target';
    const player = document.createElement('div');
    player.className = 'device-video-player';
    mockRect(shell, { top: 80, left: 0, width: 400, height: 240 });
    mockRect(player, { top: 80, left: 0, width: 400, height: 225 });
    shell.appendChild(player);
    document.body.appendChild(shell);

    transition.armEnter({
      deviceId: 'device-1',
      displayName: 'Sala',
      thumbnailUrl: 'https://example.com/thumb.jpg',
      imageFailed: false,
      bounds: { top: 120, left: 24, width: 160, height: 100 },
      borderRadius: 12,
    });
    transition.notifyReady();
    fixture.detectChanges();

    expect(
      fixture.nativeElement.querySelector('[data-testid="device-detail-flying-thumb"]'),
    ).toBeTruthy();
    expect(fixture.nativeElement.querySelector('[data-testid="device-detail-scrim"]')).toBeNull();
    expect(transition.kind()).toBe('enter');
    expect(transition.settled()).toBe(false);
  });

  it('starts exit overlay without scrim when ready', async () => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: () => ({
        matches: false,
        media: '',
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
      }),
    });

    const frame = document.createElement('div');
    frame.dataset['deviceId'] = 'device-1';
    const thumb = document.createElement('div');
    thumb.className = 'device-card__thumb';
    mockRect(thumb, { top: 180, left: 16, width: 360, height: 200 });
    frame.appendChild(thumb);
    document.body.appendChild(frame);

    transition.armExit({
      deviceId: 'device-1',
      displayName: 'Sala',
      thumbnailUrl: 'https://example.com/thumb.jpg',
      imageFailed: false,
      bounds: { top: 80, left: 0, width: 400, height: 225 },
      borderRadius: 12,
    });
    transition.notifyReady();
    fixture.detectChanges();
    await new Promise<void>((resolve) => {
      requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
    });
    fixture.detectChanges();

    const root = fixture.nativeElement;
    const overlay =
      root.querySelector('[data-testid="device-detail-flying-thumb"]') ??
      root.querySelector('[data-testid="device-detail-bridge"]');
    expect(overlay).toBeTruthy();
    expect(fixture.nativeElement.querySelector('[data-testid="device-detail-scrim"]')).toBeNull();
    expect(transition.kind()).toBe('exit');
    expect(transition.settled()).toBe(false);
  });
});
