export interface AuthLogoBounds {
  top: number;
  left: number;
  width: number;
  height: number;
}

/** Fixed logo overlay used during logout route handoff. */
export interface HandoffLogoBounds {
  top: number;
  left: number;
  height: number;
}

export const AUTH_LOGO_MAX_HEIGHT = 240;
/** Message + panel + toggle + gaps below the logo (matches logout morph). */
export const AUTH_COLUMN_BELOW_LOGO_ESTIMATE = 320;
/** Fallback panel height until forms are measured during logout handoff. */
export const AUTH_PANEL_ESTIMATED_HEIGHT = 260;

export interface AuthHandoffLayout {
  logoHeight: number;
  columnHeight: number;
  columnTop: number;
  logoTop: number;
  logoCenterX: number;
}

/** Logout morph target aligned with the auth page flex column. */
export function measureAuthHandoffLayout(
  viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 800,
  viewportWidth = typeof window !== 'undefined' ? window.innerWidth : 400,
): AuthHandoffLayout {
  const logoHeight = Math.min(AUTH_LOGO_MAX_HEIGHT, viewportWidth * 0.55);
  const columnHeight = logoHeight + AUTH_COLUMN_BELOW_LOGO_ESTIMATE;
  const columnTop = Math.max(24, (viewportHeight - columnHeight) / 2);

  return {
    logoHeight,
    columnHeight,
    columnTop,
    logoTop: columnTop,
    logoCenterX: viewportWidth / 2,
  };
}

function readElementBounds(selector: string): AuthLogoBounds | null {
  if (typeof document === 'undefined') {
    return null;
  }

  const element = document.querySelector(selector);
  if (!(element instanceof HTMLElement)) {
    return null;
  }

  const rect = element.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) {
    return null;
  }

  return {
    top: rect.top,
    left: rect.left,
    width: rect.width,
    height: rect.height,
  };
}

/** Reads the auth page logo position before navigating to the shell. */
export function captureAuthLogoBounds(): AuthLogoBounds | null {
  return readElementBounds('[data-testid="auth-logo"]');
}

/** Reads the toolbar logo position before navigating to auth. */
export function captureToolbarLogoBounds(): AuthLogoBounds | null {
  return readElementBounds('[data-testid="toolbar-logo"] img');
}

/** Reads the toolbar height while the shell is still mounted. */
export function captureToolbarHeight(): number | null {
  if (typeof document === 'undefined') {
    return null;
  }

  const toolbar = document.querySelector('[data-testid="app-toolbar"]');
  if (!(toolbar instanceof HTMLElement)) {
    return null;
  }

  const height = toolbar.getBoundingClientRect().height;
  return height > 0 ? height : null;
}
