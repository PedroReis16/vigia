import { AuthConfig } from 'angular-oauth2-oidc';
import { environment } from '@environments/environment';

export const authCodeFlowConfig: AuthConfig = {
  issuer: environment.oauth2.issuer,
  redirectUri: environment.oauth2.redirectUri,
  clientId: environment.oauth2.clientId,
  responseType: 'code',
  scope: environment.oauth2.scope,
  showDebugInformation: !environment.production,
  requireHttps: environment.production,
};
