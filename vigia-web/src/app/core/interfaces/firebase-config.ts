export interface FirebaseEnvironmentConfig {
  apiKey: string;
  authDomain: string;
  projectId: string;
  messagingSenderId: string;
  appId: string;
  /** Chave pública VAPID (Firebase Console → Cloud Messaging → Web Push certificates). */
  vapidKey: string;
  storageBucket?: string;
  measurementId?: string;
}

export function isFirebaseConfigured(config: FirebaseEnvironmentConfig): boolean {
  const hasValues = Boolean(
    config.apiKey?.trim() &&
      config.projectId?.trim() &&
      config.messagingSenderId?.trim() &&
      config.vapidKey?.trim(),
  );

  if (!hasValues) {
    return false;
  }

  const placeholders = ['YOUR_', 'your_'];
  const fields = [config.apiKey, config.projectId, config.vapidKey];
  return !fields.some((value) => placeholders.some((marker) => value.includes(marker)));
}

/** Options accepted by firebase.initializeApp (excludes vapidKey). */
export function toFirebaseAppOptions(
  config: FirebaseEnvironmentConfig,
): Record<string, string> {
  const options: Record<string, string> = {
    apiKey: config.apiKey,
    authDomain: config.authDomain,
    projectId: config.projectId,
    messagingSenderId: config.messagingSenderId,
    appId: config.appId,
  };

  if (config.storageBucket?.trim()) {
    options['storageBucket'] = config.storageBucket;
  }

  if (config.measurementId?.trim()) {
    options['measurementId'] = config.measurementId;
  }

  return options;
}

export type PushInitFailureReason =
  | 'unsupported'
  | 'not_configured'
  | 'permission_denied'
  | 'token_error';

export function describePushInitFailure(reason: PushInitFailureReason): string {
  switch (reason) {
    case 'unsupported':
      return 'Push web não suportado neste browser.';
    case 'not_configured':
      return 'Firebase web incompleto: preencha firebase.vapidKey em environment.ts (e reinicie o ng serve).';
    case 'permission_denied':
      return 'Permissão de notificação negada pelo browser.';
    case 'token_error':
      return 'Não foi possível obter token FCM. Verifique vapidKey e domínios autorizados no Firebase Console.';
  }
}
