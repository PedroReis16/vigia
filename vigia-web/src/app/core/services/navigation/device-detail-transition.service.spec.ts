import { TestBed } from '@angular/core/testing';
import { DeviceDetailTransitionService } from './device-detail-transition.service';

describe('DeviceDetailTransitionService', () => {
  let service: DeviceDetailTransitionService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(DeviceDetailTransitionService);
  });

  it('starts settled and idle', () => {
    expect(service.kind()).toBe('idle');
    expect(service.settled()).toBe(true);
    expect(service.bridgeActive()).toBe(false);
  });

  it('arms enter transition', () => {
    service.armEnter({
      deviceId: 'device-1',
      displayName: 'Sala',
      thumbnailUrl: null,
      imageFailed: false,
      bounds: { top: 10, left: 20, width: 200, height: 120 },
      borderRadius: 12,
    });

    expect(service.kind()).toBe('enter');
    expect(service.settled()).toBe(false);
    expect(service.bridgeActive()).toBe(true);
    expect(service.revealProgress()).toBe(0);
    expect(service.revealClip().rx).toBe(0);
    expect(service.snapshot()?.deviceId).toBe('device-1');
  });

  it('arms exit transition with full reveal progress', () => {
    service.armExit({
      deviceId: 'device-1',
      displayName: 'Sala',
      thumbnailUrl: null,
      imageFailed: false,
      bounds: { top: 80, left: 0, width: 400, height: 225 },
      borderRadius: 12,
    });

    expect(service.kind()).toBe('exit');
    expect(service.settled()).toBe(false);
    expect(service.revealProgress()).toBe(1);
    expect(service.revealClip().rx).toBeGreaterThan(0);
  });

  it('completes transition', () => {
    service.armEnter({
      deviceId: 'device-1',
      displayName: 'Sala',
      thumbnailUrl: null,
      imageFailed: false,
      bounds: { top: 0, left: 0, width: 100, height: 80 },
      borderRadius: 8,
    });

    service.beginPlayback();
    expect(service.bridgeActive()).toBe(false);

    service.complete();
    expect(service.kind()).toBe('idle');
    expect(service.settled()).toBe(true);
    expect(service.snapshot()).toBeNull();
  });
});
