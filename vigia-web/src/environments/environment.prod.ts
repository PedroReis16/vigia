import { FirebaseEnvironmentConfig } from '@core/interfaces/firebase-config';

export const environment = {
  production: true,
  defaultLanguage: 'pt-BR',
  supportedLanguages: [
    { value: 'pt-BR', label: 'Português' },
    { value: 'en-US', label: 'English' },
    { value: 'es-ES', label: 'Español' },
  ],
  apiUrl: 'https://services.vigiadeteccoes.com.br/vigia',
  streamBaseUrl: 'https://services.vigiadeteccoes.com.br',
  firebase: {
    apiKey: "",
    authDomain: "",
    projectId: "",
    storageBucket: "",
    messagingSenderId: "",
    appId: "",
    measurementId: "",
    vapidKey: "",
  } satisfies FirebaseEnvironmentConfig,
};
