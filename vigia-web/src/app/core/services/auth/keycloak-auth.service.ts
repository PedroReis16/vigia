import { Injectable } from '@angular/core';
import { environment } from '@environments/environment';
import Keycloak from 'keycloak-js';

@Injectable({
  providedIn: 'root',
})
export class KeycloakAuthService {
  private instance: Keycloak | null = null;
  private initPromise: Promise<boolean> | null = null;

  init(): Promise<boolean> {
    this.initPromise ??= this.doInit();
    return this.initPromise;
  }

  get authenticated(): boolean {
    return this.instance?.authenticated === true;
  }

  get token(): string | null {
    return this.instance?.token ?? null;
  }

  get userId(): string | null {
    const subject = this.instance?.tokenParsed?.sub;
    return typeof subject === 'string' && subject.length > 0 ? subject : null;
  }

  async login(redirectUri?: string): Promise<void> {
    await this.init();
    await this.instance?.login({ redirectUri });
  }

  async register(redirectUri?: string): Promise<void> {
    await this.init();
    await this.instance?.register({ redirectUri });
  }

  async logout(redirectUri?: string): Promise<void> {
    await this.init();
    if (!this.instance) {
      return;
    }
    await this.instance.logout({ redirectUri });
  }

  async updateToken(minValidity: number): Promise<string | null> {
    if (!this.instance?.authenticated) {
      return null;
    }

    try {
      await this.instance.updateToken(minValidity);
      return this.instance.token ?? null;
    } catch {
      return null;
    }
  }

  clearToken(): void {
    this.instance?.clearToken();
  }

  private async doInit(): Promise<boolean> {
    const { url, realm, clientId } = environment.keycloak;
    if (!url || !realm || !clientId || typeof window === 'undefined') {
      return false;
    }

    const keycloak = new Keycloak({ url, realm, clientId });
    this.instance = keycloak;
    return keycloak.init({
      onLoad: 'check-sso',
      pkceMethod: 'S256',
      checkLoginIframe: false,
      silentCheckSsoRedirectUri: `${window.location.origin}/silent-check-sso.html`,
    });
  }
}
