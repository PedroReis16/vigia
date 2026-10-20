import { vi } from 'vitest';
import {
  AUTH_ENTER_STORAGE_KEY,
  AUTH_EXIT_STORAGE_KEY,
  AUTH_HANDOFF_COOKIE,
  AUTH_LOGO_MEMORY_KEY,
  clearExitHold,
  keycloakLogoBounds,
  parseHandoffLogo,
  peekExitHold,
  resolveLogoutLogoTarget,
  stageAppExit,
  stageKeycloakExit,
  takeEnterHandoff,
} from './auth-page-handoff';

describe('auth page handoff', () => {
  const memory = new Map<string, string>();

  beforeEach(() => {
    memory.clear();
    sessionStorage.clear();
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => memory.get(key) ?? null,
      setItem: (key: string, value: string) => memory.set(key, value),
      removeItem: (key: string) => memory.delete(key),
      clear: () => memory.clear(),
    });
    document.cookie = `${AUTH_HANDOFF_COOKIE}=; Path=/; Max-Age=0`;
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('parses a logo box and rejects an empty one', () => {
    expect(parseHandoffLogo('10,20,225,225')).toEqual({
      top: 10,
      left: 20,
      width: 225,
      height: 225,
    });
    expect(parseHandoffLogo('10,20,0,225')).toBeNull();
    expect(parseHandoffLogo('nope')).toBeNull();
  });

  it('places the Keycloak logo in a centered square', () => {
    const desktop = keycloakLogoBounds(1440, 900);
    expect(desktop.width).toBe(225);
    expect(desktop.height).toBe(225);
    expect(desktop.left).toBe((1440 - 225) / 2);
    expect(desktop.top).toBeGreaterThan(24);

    const mobile = keycloakLogoBounds(390, 844);
    expect(mobile.height).toBeLessThanOrEqual(175);
    expect(mobile.left).toBe((390 - mobile.width) / 2);
  });

  it('remembers a login logo and ignores register for the logout target', () => {
    sessionStorage.setItem(AUTH_ENTER_STORAGE_KEY, '12,40,225,225,1440,900,login');

    const enter = takeEnterHandoff();

    expect(enter).toMatchObject({ top: 12, left: 40, width: 225, height: 225, mode: 'login' });
    expect(sessionStorage.getItem(AUTH_ENTER_STORAGE_KEY)).toBeNull();
    expect(resolveLogoutLogoTarget(1440, 900)).toMatchObject({ top: 12, left: 40 });
    expect(resolveLogoutLogoTarget(800, 600).width).toBe(225);

    sessionStorage.setItem(AUTH_ENTER_STORAGE_KEY, '4,8,180,180,390,844,register');
    expect(takeEnterHandoff()).toMatchObject({ mode: 'register' });
    expect(localStorage.getItem(AUTH_LOGO_MEMORY_KEY)).toBe('12,40,225,225,1440,900');
  });

  it('treats a missing measurement as a fallback', () => {
    sessionStorage.setItem(AUTH_ENTER_STORAGE_KEY, 'fallback');
    expect(takeEnterHandoff()).toBe('fallback');
  });

  it('keeps the logout logo until Keycloak is ready to reveal the form', () => {
    stageAppExit({ top: 180, left: 300, width: 225, height: 225 });
    expect(peekExitHold()).toEqual({ top: 180, left: 300, width: 225, height: 225 });

    stageKeycloakExit({ top: 180, left: 300, width: 225, height: 225 });
    expect(document.cookie).toContain(`${AUTH_HANDOFF_COOKIE}=exit`);

    clearExitHold();
    expect(sessionStorage.getItem(AUTH_EXIT_STORAGE_KEY)).toBeNull();
    localStorage.removeItem(AUTH_LOGO_MEMORY_KEY);
  });
});