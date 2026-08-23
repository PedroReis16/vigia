import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';

import { routes } from './app.routes';
import { provideOptimus } from '@openng/optimus-ui/config';
import { provideTranslateService, TranslateLoader } from '@ngx-translate/core';
import {
  HTTP_INTERCEPTORS,
  HttpClient,
  provideHttpClient,
  withInterceptorsFromDi,
} from '@angular/common/http';
import { TranslateHttpLoader } from '@ngx-translate/http-loader';
import { VigiaTheme } from './shared/theme/vigia.theme';
import { environment } from '@environments/environment';
import { ApiBaseUrlInterceptor, AuthInterceptor } from '@core/interceptors';

export function HttpLoaderFactory(http: HttpClient) {
  return new TranslateHttpLoader(http, './i18n/', '.json');
}

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideAnimationsAsync(),
    provideOptimus({
      theme: {
        preset: VigiaTheme,
        options: {
          darkModeSelector: '.vigia-dark',
        },
      },
    }),
    provideHttpClient(withInterceptorsFromDi()),
    provideTranslateService({
      defaultLanguage: localStorage.getItem('language') || environment.defaultLanguage || 'pt-BR',
      loader: {
        provide: TranslateLoader,
        useFactory: HttpLoaderFactory,
        deps: [HttpClient],
      },
    }),
    {
      provide: HTTP_INTERCEPTORS,
      useClass: ApiBaseUrlInterceptor,
      multi: true,
    },
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AuthInterceptor,
      multi: true,
    },
  ],
};
