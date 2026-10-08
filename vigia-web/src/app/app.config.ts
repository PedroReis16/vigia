import { ApplicationConfig, inject, provideAppInitializer, provideZoneChangeDetection } from '@angular/core';
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
import { KeycloakAuthService } from '@core/services/auth/keycloak-auth.service';
import { AuthExitTransitionService } from '@core/services/auth/auth-exit-transition.service';
import {
  clearExitHold,
  dismissAuthBootLogo,
  keycloakLogoBounds,
  peekExitHold,
  stageKeycloakExit,
  takeEnterHandoff,
} from '@core/helpers';
import { BeginKeycloakAuthService } from '@core/usecases';

export function HttpLoaderFactory(http: HttpClient) {
  return new TranslateHttpLoader(http, './i18n/', '.json');
}

function bootstrapAuthPageHandoff(): Promise<boolean> {
  const transition = inject(AuthExitTransitionService);
  const keycloak = inject(KeycloakAuthService);
  const beginAuth = inject(BeginKeycloakAuthService);
  const enter = takeEnterHandoff();
  const exit = peekExitHold();

  if (enter && typeof window !== 'undefined') {
    const logo =
      enter === 'fallback'
        ? keycloakLogoBounds(window.innerWidth, window.innerHeight)
        : enter;
    if (enter !== 'fallback' && enter.mode === 'register') {
      transition.armRegister(logo);
    } else {
      transition.armLogin(logo);
    }
  } else if (exit) {
    transition.holdBridge();
  }

  return keycloak.init().then(async (authenticated) => {
    if (!exit) {
      return authenticated;
    }

    if (authenticated) {
      dismissAuthBootLogo();
      clearExitHold();
      transition.complete();
      return authenticated;
    }

    clearExitHold();
    stageKeycloakExit(exit);
    try {
      await beginAuth.execute('login', '/devices');
    } catch {
      dismissAuthBootLogo();
      transition.complete();
    }
    return authenticated;
  });
}

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideAppInitializer(() => bootstrapAuthPageHandoff()),
    provideRouter(routes),
    provideAnimationsAsync(),
    provideOptimus({
      theme: {
        preset: VigiaTheme,
        options: {
          // Light-only — same as Flutter ThemeMode.light
          darkModeSelector: false,
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
