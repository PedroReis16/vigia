export interface ElementBounds {
  top: number;
  left: number;
  width: number;
  height: number;
}

export function boundsFromRect(rect: DOMRect): ElementBounds {
  return {
    top: rect.top,
    left: rect.left,
    width: rect.width,
    height: rect.height,
  };
}

export function readElementBounds(element: Element | null | undefined): ElementBounds | null {
  if (!(element instanceof HTMLElement)) {
    return null;
  }

  const rect = element.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) {
    return null;
  }

  return boundsFromRect(rect);
}

export function readBoundsBySelector(selector: string): ElementBounds | null {
  if (typeof document === 'undefined') {
    return null;
  }

  return readElementBounds(document.querySelector(selector));
}

export function lerpBounds(start: ElementBounds, end: ElementBounds, t: number): ElementBounds {
  return {
    top: lerp(start.top, end.top, t),
    left: lerp(start.left, end.left, t),
    width: lerp(start.width, end.width, t),
    height: lerp(start.height, end.height, t),
  };
}

export function lerp(start: number, end: number, t: number): number {
  return start + (end - start) * t;
}

export function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

export function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

const BOUNDS_EPSILON = 0.5;

export function boundsNearlyEqual(a: ElementBounds, b: ElementBounds): boolean {
  return (
    Math.abs(a.top - b.top) <= BOUNDS_EPSILON &&
    Math.abs(a.left - b.left) <= BOUNDS_EPSILON &&
    Math.abs(a.width - b.width) <= BOUNDS_EPSILON &&
    Math.abs(a.height - b.height) <= BOUNDS_EPSILON
  );
}

export interface EnterRevealClip {
  cx: number;
  cy: number;
  rx: number;
  ry: number;
  opacity: number;
}

/** Expanding ellipse reveal anchored on the morphing video bounds. */
export function computeEnterRevealClip(
  bounds: ElementBounds,
  progress: number,
): EnterRevealClip {
  const cx = bounds.left + bounds.width / 2;
  const cy = bounds.top + bounds.height / 2;
  const eased = easeOutCubic(Math.min(Math.max(progress, 0), 1));

  if (typeof window === 'undefined') {
    return { cx, cy, rx: 0, ry: 0, opacity: eased };
  }

  const maxRx = Math.max(cx, window.innerWidth - cx) + 32;
  const maxRy = Math.max(cy, window.innerHeight - cy) + 32;

  return {
    cx,
    cy,
    rx: lerp(0, maxRx, eased),
    ry: lerp(0, maxRy, eased),
    opacity: Math.min(1, eased * 1.15),
  };
}
