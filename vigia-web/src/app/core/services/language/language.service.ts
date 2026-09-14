import { inject, Injectable, signal } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { environment } from '@environments/environment';
import { StorageService } from '../storage/storage.service';
@Injectable({
  providedIn: 'root',
})
export class LanguageService {
  private storage = inject(StorageService);
  private translate = inject(TranslateService);

  currentLanguage = signal<string>(this.storage.getItem('language') || environment.defaultLanguage);
  availableLanguages = environment.supportedLanguages;

  getAvailableLanguages() {
    return this.availableLanguages;
  }

  getLanguage() {
    return this.currentLanguage;
  }

  setLanguage(language: string) {
    this.currentLanguage.set(language);
    this.translate.use(language);
    this.storage.setItem('language', language);
  }
}
