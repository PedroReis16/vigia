import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideRouter } from '@angular/router';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { vi } from 'vitest';
import { AuthExitTransitionService, MessageService } from '@core/services';
import { LogoutService } from '@core/usecases';
import { VigiaTheme } from '@shared/theme/vigia.theme';
import { ToolbarComponent } from './toolbar.component';

describe('ToolbarComponent', () => {
  let component: ToolbarComponent;
  let fixture: ComponentFixture<ToolbarComponent>;
  let logout: { execute: ReturnType<typeof vi.fn> };
  let authExitTransition: AuthExitTransitionService;

  beforeEach(async () => {
    logout = { execute: vi.fn().mockResolvedValue(undefined) };

    await TestBed.configureTestingModule({
      imports: [ToolbarComponent, TranslateModule.forRoot()],
      providers: [
        { provide: LogoutService, useValue: logout },
        MessageService,
        provideRouter([{ path: 'login', children: [] }]),
        provideAnimationsAsync(),
        provideOptimus({
          theme: {
            preset: VigiaTheme,
            options: { darkModeSelector: false },
          },
        }),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ToolbarComponent);
    component = fixture.componentInstance;
    authExitTransition = TestBed.inject(AuthExitTransitionService);
    authExitTransition.complete();
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render logo and user menu trigger', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('[data-testid="toolbar-logo"]')).toBeTruthy();
    expect(compiled.querySelector('[data-testid="user-menu-trigger"]')).toBeTruthy();
  });

  it('should logout via use case', async () => {
    vi.spyOn(authExitTransition, 'waitForShellExit').mockResolvedValue(undefined);
    await component.onLogout();
    expect(logout.execute).toHaveBeenCalled();
  });

  it('arms logout transition before navigating to login', async () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const toolbar = compiled.querySelector('[data-testid="app-toolbar"]') as HTMLElement;
    const logo = compiled.querySelector('[data-testid="toolbar-logo"] img') as HTMLElement;

    Object.defineProperty(toolbar, 'getBoundingClientRect', {
      value: () => ({
        top: 0,
        left: 0,
        width: 800,
        height: 80,
        right: 800,
        bottom: 80,
        x: 0,
        y: 0,
        toJSON: () => ({}),
      }),
    });
    Object.defineProperty(logo, 'getBoundingClientRect', {
      value: () => ({
        top: 12,
        left: 20,
        width: 56,
        height: 56,
        right: 76,
        bottom: 68,
        x: 20,
        y: 12,
        toJSON: () => ({}),
      }),
    });

    vi.spyOn(authExitTransition, 'waitForShellExit').mockResolvedValue(undefined);
    const navigateSpy = vi.spyOn(component['router'], 'navigate').mockResolvedValue(true);

    await component.onLogout();

    expect(authExitTransition.kind()).toBe('logout');
    expect(navigateSpy).toHaveBeenCalledWith(['/login']);
  });
});
