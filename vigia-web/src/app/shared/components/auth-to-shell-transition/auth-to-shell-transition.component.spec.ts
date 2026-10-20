import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { AuthExitTransitionService } from '@core/services';
import { AuthToShellTransitionComponent } from './auth-to-shell-transition.component';

@Component({
  standalone: true,
  imports: [AuthToShellTransitionComponent],
  template: `
    <app-auth-to-shell-transition [mode]="mode">
      <header data-testid="app-toolbar" style="height: 80px">
        <span data-testid="toolbar-logo">
          <img alt="" width="56" height="56" />
        </span>
      </header>
    </app-auth-to-shell-transition>
  `,
})
class HostComponent {
  mode: 'enter' | 'exit' = 'enter';
}

describe('AuthToShellTransitionComponent', () => {
  let fixture: ComponentFixture<HostComponent>;
  let host: HostComponent;
  let transition: AuthExitTransitionService;
  let rafCallbacks: FrameRequestCallback[];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HostComponent],
      providers: [provideRouter([])],
    }).compileComponents();

    transition = TestBed.inject(AuthExitTransitionService);
    transition.complete();

    rafCallbacks = [];
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((callback) => {
      rafCallbacks.push(callback);
      return rafCallbacks.length;
    });
    vi.spyOn(window, 'cancelAnimationFrame').mockImplementation(() => undefined);

    fixture = TestBed.createComponent(HostComponent);
    host = fixture.componentInstance;
  });

  afterEach(() => {
    transition.complete();
    vi.restoreAllMocks();
  });

  async function flushEnterPlayback(): Promise<void> {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    for (let i = 0; i < 12 && !transition.settled(); i++) {
      const pending = rafCallbacks.splice(0, rafCallbacks.length);
      if (pending.length === 0) {
        break;
      }
      pending.forEach((callback) => callback(performance.now()));
      fixture.detectChanges();
      await Promise.resolve();
    }
  }

  it('does not render overlay when transition is idle', () => {
    fixture.detectChanges();

    const root = fixture.nativeElement as HTMLElement;
    expect(root.querySelector('[data-testid="auth-shell-veil"]')).toBeNull();
  });

  it('plays login morph and completes transition', async () => {
    host.mode = 'enter';
    transition.armLogin({ top: 40, left: 100, width: 240, height: 240 });
    expect(transition.bridgeActive()).toBe(true);

    let now = 0;
    vi.spyOn(performance, 'now').mockImplementation(() => now);

    fixture.detectChanges();
    const rootAfterMount = fixture.nativeElement as HTMLElement;
    expect(rootAfterMount.querySelector('[data-testid="auth-shell-veil"]')).toBeTruthy();
    expect(transition.bridgeActive()).toBe(true);

    now = 0;
    await fixture.whenStable();
    fixture.detectChanges();

    // afterNextRender → rAF → startEnterAnimation at t=0, then advance to end.
    const firstWave = rafCallbacks.splice(0, rafCallbacks.length);
    firstWave.forEach((callback) => callback(0));
    now = 780;
    const secondWave = rafCallbacks.splice(0, rafCallbacks.length);
    secondWave.forEach((callback) => callback(780));
    await flushEnterPlayback();

    const root = fixture.nativeElement as HTMLElement;
    expect(root.querySelector('[data-testid="auth-shell-veil"]')).toBeNull();
    expect(transition.settled()).toBe(true);
    expect(transition.bridgeActive()).toBe(false);
  });

  it('keeps the enter bridge until the veil has painted', async () => {
    host.mode = 'enter';
    transition.armLogin({ top: 40, left: 100, width: 240, height: 240 });
    vi.spyOn(performance, 'now').mockReturnValue(0);

    fixture.detectChanges();
    expect(transition.bridgeActive()).toBe(true);
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="auth-shell-veil"]'),
    ).toBeTruthy();

    await fixture.whenStable();
    // before draining rAF that starts tickEnter / beginPlayback
    expect(transition.bridgeActive()).toBe(true);
  });

  it('plays logout morph on shell and notifies when toolbar expands', async () => {
    host.mode = 'exit';
    transition.armLogout({ top: 12, left: 20, width: 56, height: 56 }, 80);
    const notifySpy = vi.spyOn(transition, 'notifyShellExitReady');

    vi.spyOn(performance, 'now')
      .mockReturnValueOnce(0)
      .mockReturnValueOnce(780);

    fixture.detectChanges();

    const rootAfterMount = fixture.nativeElement as HTMLElement;
    const veil = rootAfterMount.querySelector(
      '[data-testid="auth-shell-veil"]',
    ) as HTMLElement | null;
    expect(veil).toBeTruthy();
    expect(veil?.style.height).toBe('80px');

    await Promise.resolve();
    rafCallbacks.forEach((callback) => callback(0));
    rafCallbacks.slice(1).forEach((callback) => callback(0));
    rafCallbacks.slice(2).forEach((callback) => callback(0));

    expect(notifySpy).toHaveBeenCalled();
    expect(transition.kind()).toBe('logout');
    expect(transition.handoffLogo()).not.toBeNull();
    expect(transition.bridgeActive()).toBe(true);
  });
});
