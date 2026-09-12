import { captureAuthLogoBounds, captureToolbarHeight, captureToolbarLogoBounds } from './auth-logo-bounds.helper';

describe('captureAuthLogoBounds', () => {
  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('returns null when logo is missing', () => {
    expect(captureAuthLogoBounds()).toBeNull();
  });

  it('returns bounding box for auth logo', () => {
    const logo = document.createElement('img');
    logo.dataset['testid'] = 'auth-logo';
    Object.defineProperty(logo, 'getBoundingClientRect', {
      value: () => ({
        top: 48,
        left: 120,
        width: 240,
        height: 240,
        right: 360,
        bottom: 288,
        x: 120,
        y: 48,
        toJSON: () => ({}),
      }),
    });
    document.body.appendChild(logo);

    expect(captureAuthLogoBounds()).toEqual({
      top: 48,
      left: 120,
      width: 240,
      height: 240,
    });
  });

  it('returns bounding box for toolbar logo', () => {
    const logo = document.createElement('img');
    const wrapper = document.createElement('span');
    wrapper.dataset['testid'] = 'toolbar-logo';
    Object.defineProperty(logo, 'getBoundingClientRect', {
      value: () => ({
        top: 12,
        left: 20,
        width: 56,
        height: 56,
        right: 76,
        bottom: 68,
        x: 20,
        y: 12,
        toJSON: () => ({}),
      }),
    });
    wrapper.appendChild(logo);
    document.body.appendChild(wrapper);

    expect(captureToolbarLogoBounds()).toEqual({
      top: 12,
      left: 20,
      width: 56,
      height: 56,
    });
  });

  it('returns toolbar height', () => {
    const toolbar = document.createElement('header');
    toolbar.dataset['testid'] = 'app-toolbar';
    Object.defineProperty(toolbar, 'getBoundingClientRect', {
      value: () => ({
        top: 0,
        left: 0,
        width: 800,
        height: 80,
        right: 800,
        bottom: 80,
        x: 0,
        y: 0,
        toJSON: () => ({}),
      }),
    });
    document.body.appendChild(toolbar);

    expect(captureToolbarHeight()).toBe(80);
  });
});
