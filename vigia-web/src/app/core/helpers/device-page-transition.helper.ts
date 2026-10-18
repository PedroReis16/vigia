export type DevicePageTransitionDirection = 'forward' | 'back';

export interface RouteUrlNode {
  url: readonly { path: string }[];
  firstChild: RouteUrlNode | null;
}

const DEVICE_DETAIL_PATH = /^\/devices\/([^/]+)$/;
const DEVICE_CLIPS_PATH = /^\/devices\/([^/]+)\/clips$/;

export function normalizeRouterPath(url: string): string {
  const withoutHash = url.split('#')[0] ?? '';
  const path = withoutHash.split('?')[0] ?? '';
  if (path.length > 1 && path.endsWith('/')) {
    return path.slice(0, -1);
  }
  return path.startsWith('/') ? path : `/${path}`;
}

export function routeSnapshotPath(node: RouteUrlNode | null): string {
  const parts: string[] = [];
  let current = node;
  while (current) {
    for (const segment of current.url) {
      if (segment.path) {
        parts.push(segment.path);
      }
    }
    current = current.firstChild;
  }
  return `/${parts.join('/')}`;
}

/** Forward is detail → clips. Back is clips → detail, for the same device. */
export function devicePageTransitionDirection(
  fromPath: string,
  toPath: string,
): DevicePageTransitionDirection | null {
  const from = normalizeRouterPath(fromPath);
  const to = normalizeRouterPath(toPath);
  const fromDetail = DEVICE_DETAIL_PATH.exec(from);
  const toClips = DEVICE_CLIPS_PATH.exec(to);
  if (fromDetail && toClips && fromDetail[1] === toClips[1]) {
    return 'forward';
  }

  const fromClips = DEVICE_CLIPS_PATH.exec(from);
  const toDetail = DEVICE_DETAIL_PATH.exec(to);
  if (fromClips && toDetail && fromClips[1] === toDetail[1]) {
    return 'back';
  }

  return null;
}
