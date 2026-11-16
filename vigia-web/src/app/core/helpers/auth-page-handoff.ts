import { AuthLogoBounds } from './auth-logo-bounds.helper';

/** Shared with `index.html` and the Keycloak theme script. */
export const AUTH_HANDOFF_COOKIE = 'vigia_auth_handoff';
export const AUTH_ENTER_STORAGE_KEY = 'vigia.auth.enter';
export const AUTH_EXIT_STORAGE_KEY = 'vigia.auth.exit';
export const AUTH_LOGO_MEMORY_KEY = 'vigia.auth.keycloakLogo';
export const AUTH_BOOT_LOGO_ID = 'vigia-auth-boot-logo';

const VIEWPORT_TOLERANCE_PX = 16;
const COOKIE_MAX_AGE_SECONDS = 45;

/** Login column under the Keycloak logo box (fields, button, links). */
const KEYCLOAK_CONTENT_BELOW_PX = 248;
const KEYCLOAK_PAGE_PADDING_PX = 24;

export interface KeycloakLogoMemory extends AuthLogoBounds {
  viewportWidth: number;
  viewportHeight: number;
  mode: 'login' | 'register';
}

/** Square logo inside the Keycloak header box, centered in the login column. */
export function keycloakLogoBounds(
  viewportWidth: number,
  viewportHeight: number,
): AuthLogoBounds {
  const mobile = viewportWidth <= 767;
  const boxWidth = Math.min(300, viewportWidth * 0.6875);
  const boxHeight = mobile ? 175 : 225;
  const size = Math.min(boxWidth, boxHeight);
  const column = boxHeight + 4 + KEYCLOAK_CONTENT_BELOW_PX;
  const available = Math.max(0, viewportHeight - KEYCLOAK_PAGE_PADDING_PX * 2);
  const columnTop = KEYCLOAK_PAGE_PADDING_PX + Math.max(0, (available - column) / 2);

  return {
    top: columnTop + (boxHeight - size) / 2,
    left: (viewportWidth - size) / 2,
    width: size,
    height: size,
  };
}

export function formatHandoffLogo(logo: AuthLogoBounds): string {
  return [logo.top, logo.left, logo.width, logo.height].map(round1).join(',');
}

export function parseHandoffLogo(value: string): AuthLogoBounds | null {
  const parts = value.split(',').map(Number);
  if (parts.length < 4 || parts.slice(0, 4).some((part) => !Number.isFinite(part))) {
    return null;
  }

  const [top, left, width, height] = parts;
  if (width <= 0 || height <= 0) {
    return null;
  }

  return { top, left, width, height };
}

/** Reads the callback handoff written by `index.html` and drops it. */
export function takeEnterHandoff(): KeycloakLogoMemory | 'fallback' | null {
  const raw = readStorageItem(sessionStorage, AUTH_ENTER_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  removeStorageItem(sessionStorage, AUTH_ENTER_STORAGE_KEY);
  if (raw === 'fallback') {
    return 'fallback';
  }

  const parts = raw.split(',');
  const logo = parseHandoffLogo(parts.slice(0, 4).join(','));
  if (!logo) {
    return 'fallback';
  }

  const viewportWidth = Number(parts[4]);
  const viewportHeight = Number(parts[5]);
  const mode = parts[6] === 'register' ? 'register' : 'login';
  const memory: KeycloakLogoMemory = {
    ...logo,
    viewportWidth: Number.isFinite(viewportWidth) ? viewportWidth : 0,
    viewportHeight: Number.isFinite(viewportHeight) ? viewportHeight : 0,
    mode,
  };

  if (mode === 'login' && memory.viewportWidth > 0 && memory.viewportHeight > 0) {
    writeStorageItem(
      localStorage,
      AUTH_LOGO_MEMORY_KEY,
      `${formatHandoffLogo(logo)},${memory.viewportWidth},${memory.viewportHeight}`,
    );
  }

  return memory;
}

export function peekExitHold(): AuthLogoBounds | null {
  const raw = readStorageItem(sessionStorage, AUTH_EXIT_STORAGE_KEY);
  return raw ? parseHandoffLogo(raw) : null;
}

export function stageAppExit(logo: AuthLogoBounds): void {
  writeStorageItem(sessionStorage, AUTH_EXIT_STORAGE_KEY, formatHandoffLogo(logo));
}

export function clearExitHold(): void {
  removeStorageItem(sessionStorage, AUTH_EXIT_STORAGE_KEY);
}

/** Tells the Keycloak theme to reveal the form from this logo position. */
export function stageKeycloakExit(logo: AuthLogoBounds): void {
  writeHandoffCookie(`exit,${formatHandoffLogo(logo)}`);
}

/** Logout target: last measured login logo when the viewport still matches. */
export function resolveLogoutLogoTarget(
  viewportWidth: number,
  viewportHeight: number,
): AuthLogoBounds {
  const remembered = readRememberedLoginLogo();
  if (
    remembered &&
    Math.abs(remembered.viewportWidth - viewportWidth) <= VIEWPORT_TOLERANCE_PX &&
    Math.abs(remembered.viewportHeight - viewportHeight) <= VIEWPORT_TOLERANCE_PX
  ) {
    return remembered;
  }

  return keycloakLogoBounds(viewportWidth, viewportHeight);
}

export function dismissAuthBootLogo(): void {
  if (typeof document === 'undefined') {
    return;
  }

  document.getElementById(AUTH_BOOT_LOGO_ID)?.remove();
}

function readRememberedLoginLogo(): KeycloakLogoMemory | null {
  const raw = readStorageItem(localStorage, AUTH_LOGO_MEMORY_KEY);
  if (!raw) {
    return null;
  }

  const parts = raw.split(',');
  const logo = parseHandoffLogo(parts.slice(0, 4).join(','));
  const viewportWidth = Number(parts[4]);
  const viewportHeight = Number(parts[5]);
  if (!logo || !Number.isFinite(viewportWidth) || !Number.isFinite(viewportHeight)) {
    return null;
  }

  return {
    ...logo,
    viewportWidth,
    viewportHeight,
    mode: 'login',
  };
}

function writeHandoffCookie(value: string): void {
  if (typeof document === 'undefined') {
    return;
  }

  document.cookie =
    `${AUTH_HANDOFF_COOKIE}=${encodeURIComponent(value)}; Path=/; Max-Age=${COOKIE_MAX_AGE_SECONDS}; SameSite=Lax`;
}

function readStorageItem(storage: Storage, key: string): string | null {
  try {
    if (typeof storage?.getItem !== 'function') {
      return null;
    }
    return storage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorageItem(storage: Storage, key: string, value: string): void {
  try {
    if (typeof storage?.setItem !== 'function') {
      return;
    }
    storage.setItem(key, value);
  } catch {
    // Private mode or a broken storage global should not block navigation.
  }
}

function removeStorageItem(storage: Storage, key: string): void {
  try {
    if (typeof storage?.removeItem !== 'function') {
      return;
    }
    storage.removeItem(key);
  } catch {
    // Ignore unavailable storage.
  }
}

function round1(value: number): number {
  return Math.round(value * 10) / 10;
}
