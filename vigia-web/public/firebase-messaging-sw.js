importScripts('/firebase-config.js');
importScripts('https://www.gstatic.com/firebasejs/11.6.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/11.6.0/firebase-messaging-compat.js');

const firebaseConfig = self.FIREBASE_CONFIG ?? {};
firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  const title = payload.notification?.title ?? 'Alerta de queda';
  const body = payload.notification?.body ?? '';
  const data = payload.data ?? {};

  self.clients
    .matchAll({ type: 'window', includeUncontrolled: true })
    .then((clients) => {
      clients.forEach((client) => {
        client.postMessage({
          type: 'FALL_ALERT',
          payload: data,
          notification: { title, body },
        });
      });
    });

  return self.registration.showNotification(title, {
    body,
    icon: '/images/vigia-logo.png',
    data,
  });
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const deviceId = event.notification.data?.deviceId;
  const url = deviceId ? `/devices/${deviceId}` : '/devices';

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if ('focus' in client) {
          client.postMessage({ type: 'NOTIFICATION_CLICK', deviceId });
          return client.focus();
        }
      }

      return self.clients.openWindow(url);
    }),
  );
});
