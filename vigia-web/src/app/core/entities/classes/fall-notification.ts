export type DeviceAlertType = 'fall' | 'device_offline';

export interface FallNotification {
  id: string;
  episodeId?: string;
  type: DeviceAlertType;
  deviceId: string;
  deviceName: string;
  nickname: string;
  title: string;
  body: string;
  receivedAt: string;
  read: boolean;
}

export interface FallAlertPayload {
  type?: string;
  deviceId?: string;
  deviceName?: string;
  nickname?: string;
  alertId?: string;
}

export interface FallAlertNotificationContent {
  title?: string;
  body?: string;
}
