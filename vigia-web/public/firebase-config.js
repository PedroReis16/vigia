// Local/dev: copy from firebase-config.js.example and fill real values (do not commit secrets).
// CI/prod: hydrated by .github/scripts/hydrate-firebase-web.sh from FIREBASE_WEB_CONFIG_JSON_BASE64.
self.FIREBASE_CONFIG = {
  apiKey: 'YOUR_API_KEY',
  authDomain: 'YOUR_PROJECT.firebaseapp.com',
  projectId: 'YOUR_PROJECT_ID',
  messagingSenderId: 'YOUR_MESSAGING_SENDER_ID',
  appId: 'YOUR_APP_ID',
};
