import { ComponentFixture, TestBed } from '@angular/core/testing';
import { convertToParamMap, provideRouter, ActivatedRoute } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { BehaviorSubject } from 'rxjs';
import { vi } from 'vitest';
import { LoginService, RegisterService } from '@core/usecases';
import { MessageService, AuthExitTransitionService } from '@core/services';
import { VigiaTheme } from '@shared/theme/vigia.theme';
import { AuthComponent } from './auth.component';

describe('AuthComponent', () => {
  let fixture: ComponentFixture<AuthComponent>;
  let component: AuthComponent;
  let queryParamMap$: BehaviorSubject<ReturnType<typeof convertToParamMap>>;

  async function setup(mode?: string): Promise<void> {
    queryParamMap$ = new BehaviorSubject(
      convertToParamMap(mode ? { mode } : {}),
    );

    await TestBed.configureTestingModule({
      imports: [AuthComponent, TranslateModule.forRoot()],
      providers: [
        { provide: LoginService, useValue: { execute: vi.fn() } },
        { provide: RegisterService, useValue: { execute: vi.fn() } },
        MessageService,
        provideRouter([{ path: 'devices', children: [] }]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              queryParamMap: convertToParamMap(mode ? { mode } : {}),
            },
            queryParamMap: queryParamMap$.asObservable(),
          },
        },
        provideAnimationsAsync(),
        provideOptimus({
          theme: {
            preset: VigiaTheme,
            options: { darkModeSelector: false },
          },
        }),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AuthComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }

  it('should create and render logo', async () => {
    await setup();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(component).toBeTruthy();
    expect(compiled.querySelector('[data-testid="auth-logo"]')).toBeTruthy();
    expect(compiled.querySelector('[data-testid="login-panel"]')).toBeTruthy();
    expect(compiled.querySelector('[data-mode="login"]')).toBeTruthy();
  });

  it('toggles between login and register modes', async () => {
    await setup();
    const compiled = fixture.nativeElement as HTMLElement;

    compiled
      .querySelector<HTMLButtonElement>('[data-testid="go-register"]')!
      .click();
    fixture.detectChanges();

    expect(component.mode()).toBe('register');
    expect(compiled.querySelector('[data-mode="register"]')).toBeTruthy();
    expect(
      compiled
        .querySelector('[data-testid="register-panel"]')
        ?.getAttribute('aria-hidden'),
    ).toBe('false');
    expect(
      compiled
        .querySelector('[data-testid="login-panel"]')
        ?.getAttribute('aria-hidden'),
    ).toBe('true');

    compiled
      .querySelector<HTMLButtonElement>('[data-testid="go-login"]')!
      .click();
    fixture.detectChanges();

    expect(component.mode()).toBe('login');
    expect(compiled.querySelector('[data-mode="login"]')).toBeTruthy();
  });

  it('opens register mode from ?mode=register', async () => {
    await setup('register');
    expect(component.mode()).toBe('register');
    expect(
      (fixture.nativeElement as HTMLElement).querySelector(
        '[data-mode="register"]',
      ),
    ).toBeTruthy();
  });

  it('completes logout handoff after auth page paints', async () => {
    await setup();
    const transition = TestBed.inject(AuthExitTransitionService);
    transition.armLogout(null, 80);
    transition.activateLogoutBridge();
    transition.setHandoffLogo({ top: 100, left: 120, height: 240 });

    const rafCallbacks: FrameRequestCallback[] = [];
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((callback) => {
      rafCallbacks.push(callback);
      return rafCallbacks.length;
    });

    fixture = TestBed.createComponent(AuthComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await Promise.resolve();

    const flushRaf = (): void => {
      const pending = [...rafCallbacks];
      rafCallbacks.length = 0;
      pending.forEach((callback) => callback(0));
    };

    for (let i = 0; i < 40; i += 1) {
      flushRaf();
      await Promise.resolve();
    }

    expect(component.introReady()).toBe(true);
    expect(transition.settled()).toBe(true);
    expect(transition.bridgeActive()).toBe(false);
    expect(transition.handoffLogo()).toBeNull();
  });
});
