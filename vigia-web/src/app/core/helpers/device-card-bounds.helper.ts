import {
  boundsNearlyEqual,
  ElementBounds,
  readElementBounds,
} from './element-bounds.helper';

export interface DeviceCardSnapshot {
  deviceId: string;
  displayName: string;
  thumbnailUrl: string | null;
  imageFailed: boolean;
  /** Bounds of the card thumbnail (video preview area). */
  bounds: ElementBounds;
  borderRadius: number;
}

export interface DeviceVideoTarget {
  bounds: ElementBounds;
  borderRadius: number;
}

export interface DeviceCardThumbTarget {
  bounds: ElementBounds;
  borderRadius: number;
}

const DEVICE_LIST_ROUTE = /^\/devices\/?$/;
const DEVICE_DETAIL_ROUTE = /^\/devices\/[^/]+(\/clips)?$/;
const STABLE_FRAMES_REQUIRED = 3;
const MAX_WAIT_ATTEMPTS = 30;

export function captureDeviceCardSnapshot(
  frame: HTMLElement,
  snapshot: Omit<DeviceCardSnapshot, 'bounds' | 'borderRadius'>,
): DeviceCardSnapshot | null {
  const thumb = frame.querySelector('.device-card__thumb');
  const bounds = readElementBounds(thumb);
  if (!bounds) {
    return null;
  }

  const cardShell = frame.closest('.p-card');
  const radiusSource = cardShell instanceof HTMLElement ? cardShell : frame;
  const radius = parseFloat(getComputedStyle(radiusSource).borderRadius) || 12;

  return {
    ...snapshot,
    bounds,
    borderRadius: Number.isFinite(radius) ? radius : 12,
  };
}

export function captureDeviceCardThumbBounds(deviceId: string): ElementBounds | null {
  return captureDeviceCardVideoTarget(deviceId)?.bounds ?? null;
}

/** Measures the list card thumbnail (`device-card__thumb`) for shared-element exit. */
export function captureDeviceCardVideoTarget(deviceId: string): DeviceCardThumbTarget | null {
  if (typeof document === 'undefined') {
    return null;
  }

  const frame = document.querySelector(`[data-device-id="${deviceId}"]`);
  if (!(frame instanceof HTMLElement)) {
    return null;
  }

  const thumb = frame.querySelector('.device-card__thumb');
  const bounds = readElementBounds(thumb);
  if (!bounds) {
    return null;
  }

  const cardShell = frame.closest('.p-card');
  const radiusSource = cardShell instanceof HTMLElement ? cardShell : frame;
  const radius = parseFloat(getComputedStyle(radiusSource).borderRadius) || 12;

  return {
    bounds,
    borderRadius: Number.isFinite(radius) ? radius : 12,
  };
}

export async function waitForDeviceCardThumbBounds(
  deviceId: string,
): Promise<DeviceCardThumbTarget | null> {
  let previous: DeviceCardThumbTarget | null = null;
  let stableFrames = 0;

  for (let attempt = 0; attempt < MAX_WAIT_ATTEMPTS; attempt += 1) {
    if (!isDeviceListLayoutReady()) {
      stableFrames = 0;
      previous = null;
      await nextFrame();
      continue;
    }

    const current = captureDeviceCardVideoTarget(deviceId);
    if (current && previous && boundsNearlyEqual(current.bounds, previous.bounds)) {
      stableFrames += 1;
      if (stableFrames >= STABLE_FRAMES_REQUIRED) {
        return current;
      }
    } else {
      stableFrames = current ? 1 : 0;
    }

    previous = current;
    await nextFrame();
  }

  return previous;
}

export function fallbackListCardThumbTarget(origin: ElementBounds): DeviceCardThumbTarget {
  if (typeof window === 'undefined') {
    return {
      bounds: origin,
      borderRadius: 12,
    };
  }

  const width = Math.min(origin.width, window.innerWidth - 32);
  const height = width * (9 / 16);

  return {
    bounds: {
      top: window.innerHeight * 0.2,
      left: (window.innerWidth - width) / 2,
      width,
      height,
    },
    borderRadius: 12,
  };
}

/** Measures the detail page video player shell (16:9 content inside `device-detail__video-inner`). */
export function captureDeviceDetailVideoTarget(): DeviceVideoTarget | null {
  if (typeof document === 'undefined') {
    return null;
  }

  const shell = document.querySelector('[data-testid="device-detail-video-target"]');
  if (!(shell instanceof HTMLElement)) {
    return null;
  }

  const content =
    shell.querySelector('.device-video-player') instanceof HTMLElement
      ? shell.querySelector('.device-video-player')
      : shell;

  const bounds = readElementBounds(content);
  if (!bounds) {
    return null;
  }

  const radius = parseFloat(getComputedStyle(shell).borderRadius) || 0;

  return {
    bounds,
    borderRadius: Number.isFinite(radius) ? radius : 0,
  };
}

function isDeviceDetailLayoutReady(): boolean {
  if (typeof document === 'undefined' || typeof window === 'undefined') {
    return false;
  }

  const path = window.location.pathname;
  if (!DEVICE_DETAIL_ROUTE.test(path)) {
    return false;
  }

  return captureDeviceDetailVideoTarget() !== null;
}

function isDeviceListLayoutReady(): boolean {
  if (typeof document === 'undefined' || typeof window === 'undefined') {
    return false;
  }

  const path = window.location.pathname;
  if (!DEVICE_LIST_ROUTE.test(path)) {
    return false;
  }

  return document.querySelector('[data-testid="devices-list"]') instanceof HTMLElement;
}

export async function waitForDeviceDetailVideoTarget(): Promise<DeviceVideoTarget | null> {
  let previous: DeviceVideoTarget | null = null;
  let stableFrames = 0;

  for (let attempt = 0; attempt < MAX_WAIT_ATTEMPTS; attempt += 1) {
    if (!isDeviceDetailLayoutReady()) {
      stableFrames = 0;
      previous = null;
      await nextFrame();
      continue;
    }

    const current = captureDeviceDetailVideoTarget();
    if (current && previous && boundsNearlyEqual(current.bounds, previous.bounds)) {
      stableFrames += 1;
      if (stableFrames >= STABLE_FRAMES_REQUIRED) {
        return current;
      }
    } else {
      stableFrames = current ? 1 : 0;
    }

    previous = current;
    await nextFrame();
  }

  return previous;
}

export async function waitForStableDeviceDetailVideoTarget(
  maxAttempts = 20,
): Promise<DeviceVideoTarget | null> {
  let previous: DeviceVideoTarget | null = null;
  let stableFrames = 0;

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const current = captureDeviceDetailVideoTarget();
    if (current && previous && boundsNearlyEqual(current.bounds, previous.bounds)) {
      stableFrames += 1;
      if (stableFrames >= STABLE_FRAMES_REQUIRED) {
        return current;
      }
    } else {
      stableFrames = current ? 1 : 0;
    }

    previous = current;
    await nextFrame();
  }

  return previous;
}

export function fallbackDeviceDetailVideoTarget(isMobile: boolean): DeviceVideoTarget {
  if (typeof window === 'undefined') {
    return {
      bounds: { top: 0, left: 0, width: 0, height: 0 },
      borderRadius: 0,
    };
  }

  const width = isMobile ? window.innerWidth : Math.min(window.innerWidth - 96, 960);
  const height = width * (9 / 16);
  const top = isMobile ? 56 : 120;
  const left = isMobile ? 0 : (window.innerWidth - width) / 2;

  return {
    bounds: { top, left, width, height },
    borderRadius: isMobile ? 0 : 12,
  };
}

function nextFrame(): Promise<void> {
  return new Promise((resolve) => {
    requestAnimationFrame(() => resolve());
  });
}
