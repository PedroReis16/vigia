import { signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { vi } from 'vitest';
import { HomeComponent } from './home.component';
import { ThemeService } from '@core/services/theme/theme.service';
import { LanguageService } from '@core/services/language/language.service';
import { Oauth2Service } from '@core/services';
import { InputComponent } from '@shared/components/input/input.component';
import { VigiaTheme } from '@shared/theme/vigia.theme';

describe('HomeComponent', () => {
  let component: HomeComponent;
  let fixture: ComponentFixture<HomeComponent>;
  let themeService: {
    setTheme: ReturnType<typeof vi.fn>;
    selectedTheme: ReturnType<typeof signal>;
  };
  let languageService: {
    setLanguage: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    const selectedTheme = signal('dark');
    const themeSpy = {
      setTheme: vi.fn((theme: string) => selectedTheme.set(theme)),
      selectedTheme,
      availableThemes: [
        { label: 'SETTINGS.THEME.LIGHT', value: 'light', isLabelTranslated: true },
        { label: 'SETTINGS.THEME.DARK', value: 'dark', isLabelTranslated: true },
      ],
    };

    const languageSpy = {
      setLanguage: vi.fn(),
      getLanguage: vi.fn(() => () => 'pt'),
      getAvailableLanguages: vi.fn(() => [
        { value: 'pt', label: 'Português' },
        { value: 'en', label: 'English' },
        { value: 'es', label: 'Español' },
      ]),
    };

    const oauthSpy = { getAccessToken: vi.fn().mockResolvedValue('token') };

    await TestBed.configureTestingModule({
      imports: [HomeComponent, TranslateModule.forRoot(), InputComponent],
      providers: [
        { provide: ThemeService, useValue: themeSpy },
        { provide: LanguageService, useValue: languageSpy },
        { provide: Oauth2Service, useValue: oauthSpy },
        provideAnimationsAsync(),
        provideOptimus({
          theme: {
            preset: VigiaTheme,
            options: { darkModeSelector: '.vigia-dark' },
          },
        }),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(HomeComponent);
    component = fixture.componentInstance;
    themeService = TestBed.inject(ThemeService) as unknown as typeof themeSpy;
    languageService = TestBed.inject(LanguageService) as unknown as typeof languageSpy;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with available languages', () => {
    expect(component.availableLanguages).toEqual([
      { value: 'pt', label: 'Português' },
      { value: 'en', label: 'English' },
      { value: 'es', label: 'Español' },
    ]);
  });

  it('should change language when changeLanguage is called', () => {
    const newLanguage = { value: 'en' };
    component.changeLanguage(newLanguage);
    expect(languageService.setLanguage).toHaveBeenCalledWith('en');
  });

  it('should show dark theme button when in light theme', () => {
    themeService.selectedTheme.set('light');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const themeButton = compiled.querySelector('[data-testid="theme-toggle"]') as HTMLElement;
    expect(themeButton).toBeTruthy();
    themeButton.click();
    expect(themeService.setTheme).toHaveBeenCalledWith('dark');
  });

  it('should show light theme button when in dark theme', () => {
    themeService.selectedTheme.set('dark');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const themeButton = compiled.querySelector('[data-testid="theme-toggle"]') as HTMLElement;
    expect(themeButton).toBeTruthy();
    themeButton.click();
    expect(themeService.setTheme).toHaveBeenCalledWith('light');
  });

  it('should call setTheme when theme button is clicked', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const themeButton = compiled.querySelector('[data-testid="theme-toggle"]') as HTMLElement;
    themeButton?.click();
    expect(themeService.setTheme).toHaveBeenCalled();
  });
});
