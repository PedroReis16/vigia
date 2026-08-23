export const environment = {
  production: true,
  defaultLanguage: 'pt-BR',
  supportedLanguages: [
    { value: 'pt-BR', label: 'Português' },
    { value: 'en-US', label: 'English' },
    { value: 'es-ES', label: 'Español' },
  ],
  apiUrl: 'https://services.vigiadeteccoes.com.br/vigia',
  oauth2: {
    issuer: '',
    redirectUri: typeof window !== 'undefined' ? `${window.location.origin}/callback` : '',
    clientId: '',
    scope: 'openid profile email',
    refreshTokenTimeThreshold: 60_000,
  },
};
