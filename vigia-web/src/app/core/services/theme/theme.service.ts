import { inject, Injectable, signal } from '@angular/core';
import { StorageService } from '../storage/storage.service';

/**
 * Light-only theme, matching Flutter `ThemeMode.light`.
 * Clears any leftover dark-mode class / preference from earlier builds.
 */
@Injectable({
  providedIn: 'root',
})
export class ThemeService {
  readonly selectedTheme = signal<'light'>('light');

  private readonly storage = inject(StorageService);

  constructor() {
    this.applyLightTheme();
  }

  /** Always light — kept for API compatibility with older call sites. */
  setTheme(_theme?: string): void {
    this.applyLightTheme();
  }

  private applyLightTheme(): void {
    document.documentElement.classList.remove('vigia-dark');
    this.selectedTheme.set('light');
    this.storage.setItem('theme', 'light');
  }
}
