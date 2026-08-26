import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideRouter } from '@angular/router';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { vi } from 'vitest';
import { MessageService } from '@core/services';
import { LogoutService } from '@core/usecases';
import { VigiaTheme } from '@shared/theme/vigia.theme';
import { ToolbarComponent } from './toolbar.component';

describe('ToolbarComponent', () => {
  let component: ToolbarComponent;
  let fixture: ComponentFixture<ToolbarComponent>;
  let logout: { execute: ReturnType<typeof vi.fn> };

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
            options: { darkModeSelector: '.vigia-dark' },
          },
        }),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ToolbarComponent);
    component = fixture.componentInstance;
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
    await component.onLogout();
    expect(logout.execute).toHaveBeenCalled();
  });
});
