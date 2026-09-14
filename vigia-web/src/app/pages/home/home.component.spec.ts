import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideOptimus } from '@openng/optimus-ui/config';
import { TranslateModule } from '@ngx-translate/core';
import { vi } from 'vitest';
import { HomeComponent } from './home.component';
import { LanguageService } from '@core/services/language/language.service';
import { InputComponent } from '@shared/components/input/input.component';
import { VigiaTheme } from '@shared/theme/vigia.theme';

describe('HomeComponent', () => {
  let component: HomeComponent;
  let fixture: ComponentFixture<HomeComponent>;
  let languageService: {
    setLanguage: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    const languageSpy = {
      setLanguage: vi.fn(),
      getLanguage: vi.fn(() => () => 'pt'),
      getAvailableLanguages: vi.fn(() => [
        { value: 'pt', label: 'Português' },
        { value: 'en', label: 'English' },
        { value: 'es', label: 'Español' },
      ]),
    };

    await TestBed.configureTestingModule({
      imports: [HomeComponent, TranslateModule.forRoot(), InputComponent],
      providers: [
        { provide: LanguageService, useValue: languageSpy },
        provideAnimationsAsync(),
        provideOptimus({
          theme: {
            preset: VigiaTheme,
            options: { darkModeSelector: false },
          },
        }),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(HomeComponent);
    component = fixture.componentInstance;
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
});
