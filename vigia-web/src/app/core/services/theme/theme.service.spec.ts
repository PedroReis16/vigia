import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { StorageService } from '../storage/storage.service';
import { ThemeService } from './theme.service';

describe('ThemeService', () => {
  let service: ThemeService;
  let htmlElement: HTMLElement;
  let storage: { getItem: ReturnType<typeof vi.fn>; setItem: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    htmlElement = document.documentElement;
    htmlElement.classList.add('vigia-dark');
    storage = {
      getItem: vi.fn(() => 'dark'),
      setItem: vi.fn(),
    };
    TestBed.configureTestingModule({
      providers: [{ provide: StorageService, useValue: { ...storage, removeItem: vi.fn() } }],
    });
    service = TestBed.inject(ThemeService);
  });

  afterEach(() => {
    htmlElement.classList.remove('vigia-dark');
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should force light theme on init even if dark was stored', () => {
    expect(service.selectedTheme()).toBe('light');
    expect(htmlElement.classList.contains('vigia-dark')).toBe(false);
    expect(storage.setItem).toHaveBeenCalledWith('theme', 'light');
  });

  it('should keep light when setTheme is called with dark', () => {
    service.setTheme('dark');
    expect(service.selectedTheme()).toBe('light');
    expect(htmlElement.classList.contains('vigia-dark')).toBe(false);
  });
});
