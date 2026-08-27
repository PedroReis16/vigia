import { FirebaseEnvironmentConfig } from '@core/interfaces/firebase-config';

export const environment = {
  production: true,
  defaultLanguage: 'pt-BR',
  supportedLanguages: [
    { value: 'pt-BR', label: 'Português' },
    { value: 'en-US', label: 'English' },
    { value: 'es-ES', label: 'Español' },
  ],
  apiUrl: 'http://localhost:81/vigia',
  streamBaseUrl: 'http://localhost:81',

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
