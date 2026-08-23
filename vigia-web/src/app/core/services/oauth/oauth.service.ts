import { inject, Injectable } from '@angular/core';
import { authCodeFlowConfig } from '@core/config/oauth/auth.config';
import { environment } from '@environments/environment';
import { OAuthService } from 'angular-oauth2-oidc';

@Injectable({
  providedIn: 'root',
})
export class Oauth2Service {
  oauthService = inject(OAuthService);
  isLoaded = false;
  promiseRefreshToken: Promise<string> | null = null;

  constructor() {
    this.configure();
  }

  async configure() {
    if (this.isLoaded) {
      return;
    }

    this.oauthService.configure(authCodeFlowConfig);
    await this.oauthService.loadDiscoveryDocument();

    this.isLoaded = true;
  }

  async login() {
    await this.configure();
    this.oauthService.initLoginFlow();
  }

  async logout() {
    await this.configure();

    await this.oauthService.revokeTokenAndLogout({
      token_type_hint: 'refresh_token',
      token: this.oauthService.getRefreshToken(),
    });
  }

  async handleCallback() {
    await this.configure();

    await this.oauthService.tryLogin({
      disableNonceCheck: true,
    });
  }

  async getUser() {
    await this.configure();
    return this.oauthService.getIdentityClaims();
  }

  async isLoggedIn() {
    const user = await this.getUser();

    return !!user;
  }

  async getAccessToken() {
    await this.configure();

    if (this.promiseRefreshToken) {
      return await this.promiseRefreshToken;
    }

    const tokenExp = this.oauthService.getAccessTokenExpiration();
    const now = new Date();
    const diff = tokenExp - now.getTime();

    if (diff < environment.oauth2.refreshTokenTimeThreshold) {
      this.promiseRefreshToken = this.oauthService.refreshToken().then(() => {
        return this.oauthService.getAccessToken();
      });

      return await this.promiseRefreshToken;
    }

    return this.oauthService.getAccessToken();
  }

  async getRefreshToken() {
    await this.configure();
    return this.oauthService.getRefreshToken();
  }
}
