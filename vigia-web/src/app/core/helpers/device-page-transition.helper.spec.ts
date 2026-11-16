import {
  devicePageTransitionDirection,
  normalizeRouterPath,
  routeSnapshotPath,
  type RouteUrlNode,
} from './device-page-transition.helper';

function node(...paths: string[]): RouteUrlNode {
  return {
    url: paths.map((path) => ({ path })),
    firstChild: null,
  };
}

describe('devicePageTransitionDirection', () => {
  it('treats detail to clips as forward for the same device', () => {
    expect(devicePageTransitionDirection('/devices/device-1', '/devices/device-1/clips')).toBe(
      'forward',
    );
  });

  it('treats clips to detail as back for the same device', () => {
    expect(
      devicePageTransitionDirection('/devices/device-1/clips?from=detail', '/devices/device-1/'),
    ).toBe('back');
  });

  it('ignores other device navigations', () => {
    expect(devicePageTransitionDirection('/devices', '/devices/device-1')).toBeNull();
    expect(devicePageTransitionDirection('/devices/device-1', '/devices/device-2/clips')).toBeNull();
    expect(devicePageTransitionDirection('/devices/device-1/clips', '/home')).toBeNull();
  });
});

describe('routeSnapshotPath', () => {
  it('joins url segments from the route tree', () => {
    const root: RouteUrlNode = {
      url: [],
      firstChild: {
        url: [],
        firstChild: node('devices', 'device-1', 'clips'),
      },
    };

    expect(routeSnapshotPath(root)).toBe('/devices/device-1/clips');
  });
});

describe('normalizeRouterPath', () => {
  it('drops query, hash and a trailing slash', () => {
    expect(normalizeRouterPath('/devices/device-1/clips/?x=1#top')).toBe('/devices/device-1/clips');
  });
});
