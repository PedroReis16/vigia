import { FirebaseEnvironmentConfig } from '@core/interfaces/firebase-config';

/** Copy values into environment.ts / environment.prod.ts and public/firebase-config.js */
export const firebaseConfigExample: FirebaseEnvironmentConfig = {
  apiKey: 'YOUR_API_KEY',
  authDomain: 'YOUR_PROJECT.firebaseapp.com',
  projectId: 'YOUR_PROJECT_ID',
  messagingSenderId: 'YOUR_MESSAGING_SENDER_ID',
  appId: 'YOUR_APP_ID',
  vapidKey: 'YOUR_VAPID_PUBLIC_KEY',
};
