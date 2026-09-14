import { TestBed } from '@angular/core/testing';
import { AuthExitTransitionService } from './auth-exit-transition.service';

describe('AuthExitTransitionService', () => {
  let service: AuthExitTransitionService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AuthExitTransitionService);
    service.complete();
  });

  it('starts settled and idle', () => {
    expect(service.kind()).toBe('idle');
    expect(service.isArmed()).toBe(false);
    expect(service.settled()).toBe(true);
  });

  it('arms login transition with bridge overlay', () => {
    service.armLogin({ top: 10, left: 20, width: 240, height: 240 });

    expect(service.kind()).toBe('login');
    expect(service.isArmed()).toBe(true);
    expect(service.settled()).toBe(false);
    expect(service.bridgeActive()).toBe(true);
    expect(service.logoOrigin()).toEqual({
      top: 10,
      left: 20,
      width: 240,
      height: 240,
    });
  });

  it('arms logout transition with toolbar height', () => {
    service.armLogout({ top: 12, left: 20, width: 56, height: 56 }, 80);

    expect(service.kind()).toBe('logout');
    expect(service.bridgeActive()).toBe(false);
    expect(service.toolbarHeight()).toBe(80);
    expect(service.toolbarLogoRevealed()).toBe(false);
    expect(service.settled()).toBe(false);
  });

  it('isLogoutHandoff when bridge covers logout navigation', () => {
    service.armLogout(null, 80);
    service.activateLogoutBridge();
    expect(service.isLogoutHandoff()).toBe(true);
    service.complete();
    expect(service.isLogoutHandoff()).toBe(false);
  });

  it('reveals toolbar logo before morph settles', () => {
    service.armLogin(null);
    service.revealToolbarLogo();
    expect(service.toolbarLogoRevealed()).toBe(true);
    expect(service.settled()).toBe(false);
  });

  it('resolves waitForShellExit when shell morph completes', async () => {
    service.armLogout(null, 80);
    const done = service.waitForShellExit();

    service.notifyShellExitReady();
    await expect(done).resolves.toBeUndefined();
  });

  it('completes transition', () => {
    service.armRegister(null);
    service.setHandoffLogo({ top: 10, left: 20, height: 240 });
    service.complete();

    expect(service.kind()).toBe('idle');
    expect(service.logoOrigin()).toBeNull();
    expect(service.toolbarHeight()).toBeNull();
    expect(service.bridgeActive()).toBe(false);
    expect(service.handoffLogo()).toBeNull();
    expect(service.authHandoffReleased()).toBe(false);
    expect(service.settled()).toBe(true);
  });

  it('keeps app handoff logo until auth page releases it', () => {
    service.armLogout(null, 80);
    service.setHandoffLogo({ top: 10, left: 20, height: 240 });
    service.activateLogoutBridge();

    expect(service.showAppHandoffLogo()).toBe(true);

    service.releaseAuthHandoff();
    expect(service.showAppHandoffLogo()).toBe(false);
    expect(service.authHandoffReleased()).toBe(true);
  });
});
