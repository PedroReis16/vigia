import {
  captureDeviceCardVideoTarget,
  captureDeviceDetailVideoTarget,
  waitForDeviceCardThumbBounds,
  waitForDeviceDetailVideoTarget,
} from './device-card-bounds.helper';

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

describe('captureDeviceDetailVideoTarget', () => {
  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('returns null when video target is missing', () => {
    expect(captureDeviceDetailVideoTarget()).toBeNull();
  });

  it('measures the 16:9 player inside the video shell', () => {
    const shell = document.createElement('div');
    shell.dataset['testid'] = 'device-detail-video-target';
    Object.defineProperty(shell, 'getBoundingClientRect', {
      value: () => ({
        top: 40,
        left: 0,
        width: 400,
        height: 260,
        right: 400,
        bottom: 300,
        x: 0,
        y: 40,
        toJSON: () => ({}),
      }),
    });

    const player = document.createElement('div');
    player.className = 'device-video-player';
    mockRect(player, { top: 56, left: 16, width: 368, height: 207 });

    shell.appendChild(player);
    document.body.appendChild(shell);

    expect(captureDeviceDetailVideoTarget()).toEqual({
      bounds: { top: 56, left: 16, width: 368, height: 207 },
      borderRadius: 0,
    });
  });
});

describe('waitForDeviceDetailVideoTarget', () => {
  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('resolves when target exists without mobile layout class', async () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { pathname: '/devices/device-1' },
    });

    const shell = document.createElement('div');
    shell.dataset['testid'] = 'device-detail-video-target';
    const player = document.createElement('div');
    player.className = 'device-video-player';
    mockRect(shell, { top: 56, left: 0, width: 390, height: 240 });
    mockRect(player, { top: 56, left: 0, width: 390, height: 219 });
    shell.appendChild(player);
    document.body.appendChild(shell);

    const target = await waitForDeviceDetailVideoTarget();

    expect(target).toEqual({
      bounds: { top: 56, left: 0, width: 390, height: 219 },
      borderRadius: 0,
    });
  });
});

describe('waitForDeviceCardThumbBounds', () => {
  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('resolves when list card thumb is stable', async () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { pathname: '/devices' },
    });

    const list = document.createElement('div');
    list.dataset['testid'] = 'devices-list';
    document.body.appendChild(list);

    const frame = document.createElement('div');
    frame.dataset['deviceId'] = 'device-1';
    const thumb = document.createElement('div');
    thumb.className = 'device-card__thumb';
    mockRect(thumb, { top: 180, left: 16, width: 360, height: 200 });
    frame.appendChild(thumb);
    list.appendChild(frame);

    const target = await waitForDeviceCardThumbBounds('device-1');

    expect(target).toEqual({
      bounds: { top: 180, left: 16, width: 360, height: 200 },
      borderRadius: 12,
    });
  });
});

describe('captureDeviceCardVideoTarget', () => {
  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('measures card thumb bounds', () => {
    const frame = document.createElement('div');
    frame.dataset['deviceId'] = 'device-1';
    const thumb = document.createElement('div');
    thumb.className = 'device-card__thumb';
    mockRect(thumb, { top: 120, left: 8, width: 300, height: 170 });
    frame.appendChild(thumb);
    document.body.appendChild(frame);

    expect(captureDeviceCardVideoTarget('device-1')).toEqual({
      bounds: { top: 120, left: 8, width: 300, height: 170 },
      borderRadius: 12,
    });
  });
});
