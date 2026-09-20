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
  firebase: {
    apiKey: 'AIzaSyDLv9uHA6xFbRRnwjRmzWaCxadX-v62DvI',
    authDomain: 'vigia-fall-detection.firebaseapp.com',
    projectId: 'vigia-fall-detection',
    storageBucket: 'vigia-fall-detection.firebasestorage.app',
    messagingSenderId: '241599132191',
    appId: '1:241599132191:web:08154d96d34f15cf18db2a',
    measurementId: 'G-7DG1Q5EQP8',
    // Firebase Console → Cloud Messaging → Web Push certificates → Key pair (pública)
    vapidKey: 'BAU11UKsG0rBMlbkj5YQa4D7CmjLT6r5Zda1J7K90SoEQjZ_Ig9TLrR7PdzQqFUtD5vJqwzJeAcmW8aKt3sJe4E',
  } satisfies FirebaseEnvironmentConfig,
};
