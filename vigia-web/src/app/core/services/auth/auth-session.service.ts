import { inject, Injectable } from '@angular/core';
import { KeycloakAuthService } from './keycloak-auth.service';

@Injectable({
  providedIn: 'root',
})
export class AuthSessionService {
  private readonly keycloak = inject(KeycloakAuthService);

  isAuthenticated(): boolean {
    return this.keycloak.authenticated;
  }

  getAccessToken(): string | null {
    return this.keycloak.token;
  }

  getUserId(): string | null {
    return this.keycloak.userId;
  }

  /** Refreshes the access token when it expires within the given window. */
  ensureFreshAccessToken(minValidity = 30): Promise<string | null> {
    return this.keycloak.updateToken(minValidity);
  }

  /** Forces a refresh. Used after the API rejects the current access token. */
  forceRefreshAccessToken(): Promise<string | null> {
    return this.keycloak.updateToken(-1);
  }

  clearSession(): void {
    this.keycloak.clearToken();
  }
}
