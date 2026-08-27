import {
  FallAlertNotificationContent,
  FallAlertPayload,
  FallNotification,
} from '@core/entities/classes/fall-notification';

export function parseFallAlertPayload(
  data: FallAlertPayload,
  notification?: FallAlertNotificationContent,
): FallNotification | null {
  if (data.type !== 'fall') {
    return null;
  }

  const deviceId = data.deviceId?.trim();
  if (!deviceId) {
    return null;
  }

  const deviceName = data.deviceName?.trim() ?? '';
  const nickname = data.nickname?.trim() ?? '';
  const displayName = nickname || deviceName || deviceId;

  return {
    id: `${deviceId}-${Date.now()}`,
    type: 'fall',
    deviceId,
    deviceName,
    nickname,
    title: notification?.title?.trim() || 'Alerta de queda',
    body: notification?.body?.trim() || `Queda detectada em ${displayName}`,
    receivedAt: new Date().toISOString(),
    read: false,
  };
}

export function resolveFallAlertDeviceId(data: FallAlertPayload): string | null {
  if (data.type !== 'fall') {
    return null;
  }

  const deviceId = data.deviceId?.trim();
  return deviceId || null;
}
