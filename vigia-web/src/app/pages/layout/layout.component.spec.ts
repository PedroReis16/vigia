import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideRouter } from '@angular/router';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { vi } from 'vitest';
import { DeviceGroupsRealtimeService, MessageService } from '@core/services';
import { LogoutService } from '@core/usecases';
import { NEVER } from 'rxjs';
import { LayoutComponent } from '@pages';
import { VigiaTheme } from '@shared/theme/vigia.theme';

describe('LayoutComponent', () => {
  let component: LayoutComponent;
  let fixture: ComponentFixture<LayoutComponent>;

  beforeEach(async () => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })),
    });

    await TestBed.configureTestingModule({
      imports: [LayoutComponent, TranslateModule.forRoot()],
      providers: [
        provideRouter([]),
        provideAnimationsAsync(),
        MessageService,
        { provide: LogoutService, useValue: { execute: vi.fn().mockResolvedValue(undefined) } },
        {
          provide: DeviceGroupsRealtimeService,
          useValue: {
            membershipChanged$: NEVER,
            connect: vi.fn().mockResolvedValue(undefined),
            disconnect: vi.fn().mockResolvedValue(undefined),
          },
        },
        provideOptimus({
          theme: {
            preset: VigiaTheme,
            options: { darkModeSelector: false },
          },
        }),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LayoutComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render toolbar without sidebar', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('[data-testid="app-toolbar"]')).toBeTruthy();
    expect(compiled.querySelector('[data-testid="app-sidebar"]')).toBeNull();
  });

  it('hides toolbar when mobile device detail layout is active', () => {
    component.isMobileDeviceDetail.set(true);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const layoutRoot = compiled.querySelector('.layout') as HTMLElement;
    expect(layoutRoot.classList.contains('layout--device-detail-mobile')).toBe(true);
    expect(compiled.querySelector('[data-testid="app-toolbar"]')).toBeNull();
  });
});
