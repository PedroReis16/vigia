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

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HostComponent],
      providers: [provideRouter([])],
    }).compileComponents();

    transition = TestBed.inject(AuthExitTransitionService);
    transition.complete();

    fixture = TestBed.createComponent(HostComponent);
    host = fixture.componentInstance;
  });

  afterEach(() => {
    transition.complete();
    vi.restoreAllMocks();
  });

  it('does not render overlay when transition is idle', () => {
    fixture.detectChanges();

    const root = fixture.nativeElement as HTMLElement;
    expect(root.querySelector('[data-testid="auth-shell-veil"]')).toBeNull();
  });

    it('plays login morph and completes transition', async () => {
    host.mode = 'enter';
    transition.armLogin({ top: 40, left: 100, width: 240, height: 240 });

    const rafCallbacks: FrameRequestCallback[] = [];
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((callback) => {
      rafCallbacks.push(callback);
      return rafCallbacks.length;
    });
    vi.spyOn(window, 'cancelAnimationFrame').mockImplementation(() => undefined);
    vi.spyOn(performance, 'now')
      .mockReturnValueOnce(0)
      .mockReturnValueOnce(780);

    fixture.detectChanges();

    const rootAfterMount = fixture.nativeElement as HTMLElement;
    expect(rootAfterMount.querySelector('[data-testid="auth-shell-veil"]')).toBeTruthy();

    await Promise.resolve();
    rafCallbacks.forEach((callback) => callback(0));
    rafCallbacks.slice(1).forEach((callback) => callback(0));
    fixture.detectChanges();

    const root = fixture.nativeElement as HTMLElement;
    expect(root.querySelector('[data-testid="auth-shell-veil"]')).toBeNull();
    expect(transition.settled()).toBe(true);
    expect(transition.bridgeActive()).toBe(false);
  });

  it('plays logout morph on shell and notifies when toolbar expands', async () => {
    host.mode = 'exit';
    transition.armLogout({ top: 12, left: 20, width: 56, height: 56 }, 80);
    const notifySpy = vi.spyOn(transition, 'notifyShellExitReady');

    const rafCallbacks: FrameRequestCallback[] = [];
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((callback) => {
      rafCallbacks.push(callback);
      return rafCallbacks.length;
    });
    vi.spyOn(window, 'cancelAnimationFrame').mockImplementation(() => undefined);
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
    expect(
      rootAfterMount.querySelector('[data-testid="auth-shell-exit-backdrop"]'),
    ).toBeNull();

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
