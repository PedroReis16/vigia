import {
  DeviceAlertType,
  FallAlertNotificationContent,
  FallAlertPayload,
  FallNotification,
} from '@core/entities/classes/fall-notification';
import { UserNotificationDto } from '@core/services/http/notifications/notifications-http.service';

export function isDeviceAlertType(type: string | undefined): type is DeviceAlertType {
  return type === 'fall' || type === 'device_offline';
}

export function parseFallAlertPayload(
  data: FallAlertPayload,
  notification?: FallAlertNotificationContent,
): FallNotification | null {
  if (!isDeviceAlertType(data.type)) {
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
  const offline = data.type === 'device_offline';

  return {
    id: alertId || `${deviceId}-${Date.now()}`,
    episodeId: alertId,
    type: data.type,
    deviceId,
    deviceName,
    nickname,
    title: notification?.title?.trim() || (offline ? 'Dispositivo parado' : 'Alerta de queda'),
    body:
      notification?.body?.trim() ||
      (offline
        ? `O dispositivo ${displayName} parou de funcionar`
        : `Queda detectada em ${displayName}`),
    receivedAt: new Date().toISOString(),
    read: false,
  };
}

export function mapUserNotificationDto(dto: UserNotificationDto): FallNotification {
  return {
    id: dto.id,
    episodeId: dto.episodeId,
    type: dto.type === 'device_offline' ? 'device_offline' : 'fall',
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
  if (!isDeviceAlertType(data.type)) {
    return null;
  }

  const deviceId = data.deviceId?.trim();
  return deviceId || null;
}
