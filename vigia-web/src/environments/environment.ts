export const environment = {
  production: false,
  defaultLanguage: 'pt-BR',
  supportedLanguages: [
    { value: 'pt-BR', label: 'Português' },
    { value: 'en-US', label: 'English' },
    { value: 'es-ES', label: 'Español' },
  ],
  apiUrl: 'http://localhost:8080',
  oauth2: {
    issuer: '',
    redirectUri: typeof window !== 'undefined' ? `${window.location.origin}/callback` : '',
    clientId: '',
    scope: 'openid profile email',
    refreshTokenTimeThreshold: 60_000,
  },
};
