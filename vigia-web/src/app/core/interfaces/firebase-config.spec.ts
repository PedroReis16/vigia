import {
  describePushInitFailure,
  isFirebaseConfigured,
  toFirebaseAppOptions,
} from './firebase-config';

describe('firebase-config', () => {
  it('detects missing vapid key', () => {
    expect(
      isFirebaseConfigured({
        apiKey: 'key',
        authDomain: 'domain',
        projectId: 'project',
        messagingSenderId: 'sender',
        appId: 'app',
        vapidKey: '',
      }),
    ).toBe(false);
  });

  it('builds firebase app options without vapidKey', () => {
    expect(
      toFirebaseAppOptions({
        apiKey: 'key',
        authDomain: 'domain',
        projectId: 'project',
        messagingSenderId: 'sender',
        appId: 'app',
        vapidKey: 'vapid',
        storageBucket: 'bucket',
      }),
    ).toEqual({
      apiKey: 'key',
      authDomain: 'domain',
      projectId: 'project',
      messagingSenderId: 'sender',
      appId: 'app',
      storageBucket: 'bucket',
    });
  });

  it('describes configuration failures', () => {
    expect(describePushInitFailure('not_configured')).toContain('vapidKey');
  });
});
