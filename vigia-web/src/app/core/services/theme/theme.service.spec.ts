import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { StorageService } from '../storage/storage.service';
import { ThemeService } from './theme.service';

describe('ThemeService', () => {
  let service: ThemeService;
  let htmlElement: HTMLElement;

  beforeEach(() => {
    htmlElement = document.documentElement;
    htmlElement.classList.remove('vigia-dark');
    TestBed.configureTestingModule({
      providers: [
        {
          provide: StorageService,
          useValue: {
            getItem: vi.fn(() => 'dark'),
            setItem: vi.fn(),
            removeItem: vi.fn(),
          },
        },
      ],
    });
    service = TestBed.inject(ThemeService);
  });

  afterEach(() => {
    htmlElement.classList.remove('vigia-dark');
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should return available themes', () => {
    const themes = service.getAvailableThemes();
    expect(themes).toEqual([
      { label: 'SETTINGS.THEME.LIGHT', value: 'light', isLabelTranslated: true },
      { label: 'SETTINGS.THEME.DARK', value: 'dark', isLabelTranslated: true },
    ]);
  });

  it('should initialize with dark theme', () => {
    expect(service.selectedTheme()).toBe('dark');
    expect(htmlElement.classList.contains('vigia-dark')).toBe(true);
  });

  it('should switch to light theme', () => {
    service.setTheme('light');
    expect(service.selectedTheme()).toBe('light');
    expect(htmlElement.classList.contains('vigia-dark')).toBe(false);
  });

  it('should switch to dark theme', () => {
    service.setTheme('light');
    expect(htmlElement.classList.contains('vigia-dark')).toBe(false);

    service.setTheme('dark');
    expect(service.selectedTheme()).toBe('dark');
    expect(htmlElement.classList.contains('vigia-dark')).toBe(true);
  });
});
