import { Component, inject } from '@angular/core';
import { CardModule } from '@openng/optimus-ui/card';
import { TranslateModule } from '@ngx-translate/core';
import { ButtonModule } from '@openng/optimus-ui/button';
import { ThemeService, LanguageService } from '@core/services';
import { DividerModule } from '@openng/optimus-ui/divider';
import { InputComponent } from '@shared/components/input/input.component';

@Component({
  selector: 'app-home',
  imports: [CardModule, TranslateModule, ButtonModule, DividerModule, InputComponent],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css',
  standalone: true,
})
export class HomeComponent {
  public themeService = inject(ThemeService);
  public languageService = inject(LanguageService);
  public availableLanguages = this.languageService.getAvailableLanguages();

  changeLanguage(language: { value: string }) {
    this.languageService.setLanguage(language.value);
  }
}
