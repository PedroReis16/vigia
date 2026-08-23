import { TestBed } from '@angular/core/testing';
import { TranslateService } from '@ngx-translate/core';
import { vi } from 'vitest';
import { StorageService } from '../storage/storage.service';
import { LanguageService } from './language.service';

describe('LanguageService', () => {
  let service: LanguageService;
  let translateService: { use: ReturnType<typeof vi.fn> };
  let storage: {
    getItem: ReturnType<typeof vi.fn>;
    setItem: ReturnType<typeof vi.fn>;
    removeItem: ReturnType<typeof vi.fn>;
  };

  function setup(initialLanguage: string | null = null) {
    storage = {
      getItem: vi.fn((key: string) => (key === 'language' ? initialLanguage : null)),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    };
    const translateSpy = { use: vi.fn() };
    TestBed.configureTestingModule({
      providers: [
        LanguageService,
        { provide: TranslateService, useValue: translateSpy },
        { provide: StorageService, useValue: storage },
      ],
    });
    service = TestBed.inject(LanguageService);
    translateService = TestBed.inject(TranslateService) as unknown as typeof translateSpy;
  }

  beforeEach(() => {
    setup();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should return available languages', () => {
    const languages = service.getAvailableLanguages();
    expect(languages).toEqual([
      { value: 'pt-BR', label: 'Português' },
      { value: 'en-US', label: 'English' },
      { value: 'es-ES', label: 'Español' },
    ]);
  });

  it('should get current language from storage or default to pt-BR', () => {
    expect(service.getLanguage()()).toBe('pt-BR');

    TestBed.resetTestingModule();
    setup('en-US');
    expect(service.getLanguage()()).toBe('en-US');
  });

  it('should set new language and persist it', () => {
    service.setLanguage('en-US');
    expect(service.getLanguage()()).toBe('en-US');
    expect(storage.setItem).toHaveBeenCalledWith('language', 'en-US');
    expect(translateService.use).toHaveBeenCalledWith('en-US');
  });
});
