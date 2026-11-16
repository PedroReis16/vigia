import { inject, Injectable } from '@angular/core';
import { KeycloakAuthService } from '@core/services/auth/keycloak-auth.service';

export type KeycloakAuthMode = 'login' | 'register';

@Injectable({
  providedIn: 'root',
})
export class BeginKeycloakAuthService {
  private readonly keycloak = inject(KeycloakAuthService);

  execute(mode: KeycloakAuthMode, path = '/devices'): Promise<void> {
    const redirectUri = absoluteRedirectUri(path);
    return mode === 'register'
      ? this.keycloak.register(redirectUri)
      : this.keycloak.login(redirectUri);
  }
}

function absoluteRedirectUri(path: string): string | undefined {
  if (typeof window === 'undefined') {
    return undefined;
  }

  const origin = window.location?.origin;
  if (!origin || origin === 'null') {
    return undefined;
  }

  const normalized = path.startsWith('/') ? path : `/${path}`;
  return `${origin.replace(/\/$/, '')}${normalized}`;
}
