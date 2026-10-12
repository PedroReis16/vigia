import {
  FallAlertNotificationContent,
  FallAlertPayload,
  FallNotification,
} from '@core/entities/classes/fall-notification';
import { UserNotificationDto } from '@core/services/http/notifications/notifications-http.service';

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
  const alertId = data.alertId?.trim();

  return {
    id: alertId || `${deviceId}-${Date.now()}`,
    episodeId: alertId,
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

export function mapUserNotificationDto(dto: UserNotificationDto): FallNotification {
  return {
    id: dto.id,
    episodeId: dto.episodeId,
    type: 'fall',
    deviceId: dto.deviceId,
    deviceName: '',
    nickname: '',
    title: dto.title,
    body: dto.body,
    receivedAt: dto.createdAt,
    read: dto.read,
  };
}

export function resolveFallAlertDeviceId(data: FallAlertPayload): string | null {
  if (data.type !== 'fall') {
    return null;
  }

  const deviceId = data.deviceId?.trim();
  return deviceId || null;
}
