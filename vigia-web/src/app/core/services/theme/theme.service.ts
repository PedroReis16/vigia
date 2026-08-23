import { inject, Injectable, signal } from '@angular/core';
import { StorageService } from '../storage/storage.service';

@Injectable({
  providedIn: 'root',
})
export class ThemeService {
  selectedTheme = signal('dark');
  availableThemes = [
    { label: 'SETTINGS.THEME.LIGHT', value: 'light', isLabelTranslated: true },
    { label: 'SETTINGS.THEME.DARK', value: 'dark', isLabelTranslated: true },
  ];

  private storage = inject(StorageService);

  constructor() {
    const theme = this.storage.getItem('theme') || this.getBrowserTheme();

    if (theme) {
      this.setTheme(theme);
    }
  }

  setTheme(theme: string) {
    const element = document.querySelector('html');

    if (theme === 'dark') {
      element?.classList.add('vigia-dark');
    } else {
      element?.classList.remove('vigia-dark');
    }
    this.selectedTheme.set(theme);

    this.storage.setItem('theme', theme);
  }

  getAvailableThemes() {
    return this.availableThemes;
  }

  getBrowserTheme() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
}
