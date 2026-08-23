import { Component, inject, OnInit } from '@angular/core';
import { CardModule } from '@openng/optimus-ui/card';
import { TranslateModule } from '@ngx-translate/core';
import { ButtonModule } from '@openng/optimus-ui/button';
import { Oauth2Service, ThemeService } from '@core/services';
import { DividerModule } from '@openng/optimus-ui/divider';
import { InputComponent } from '@shared/components/input/input.component';
import { LanguageService } from '@core/services';
@Component({
  selector: 'app-home',
  imports: [CardModule, TranslateModule, ButtonModule, DividerModule, InputComponent],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css',
  standalone: true,
})
export class HomeComponent implements OnInit {
  public themeService = inject(ThemeService);
  public languageService = inject(LanguageService);
  public oauth2Service = inject(Oauth2Service);
  public availableLanguages = this.languageService.getAvailableLanguages();

  async ngOnInit(): Promise<void> {
    const accessToken = await this.oauth2Service.getAccessToken();
    console.log('accessToken', accessToken);
  }

  changeLanguage(language: { value: string }) {
    this.languageService.setLanguage(language.value);
  }
}
