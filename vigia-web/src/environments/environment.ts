import { FirebaseEnvironmentConfig } from '@core/interfaces/firebase-config';

export const environment = {
  production: false,
  defaultLanguage: 'pt-BR',
  supportedLanguages: [
    { value: 'pt-BR', label: 'Português' },
    { value: 'en-US', label: 'English' },
    { value: 'es-ES', label: 'Español' },
  ],
  apiUrl: 'http://localhost:81/vigia',
  streamBaseUrl: 'http://localhost:81',
  keycloak: {
    url: 'http://localhost:81/auth',
    realm: 'vigia',
    clientId: 'vigia-web',
  },
  // Fill locally for FCM (never commit real keys). See firebase.config.example.ts / README.
  firebase: {
    apiKey: '',
    authDomain: '',
    projectId: '',
    storageBucket: '',
    messagingSenderId: '',
    appId: '',
    measurementId: '',
    vapidKey: '',
  } satisfies FirebaseEnvironmentConfig,
};
