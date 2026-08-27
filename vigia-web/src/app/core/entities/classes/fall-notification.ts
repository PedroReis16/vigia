export interface FallNotification {
  id: string;
  type: 'fall';
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
}

export interface FallAlertNotificationContent {
  title?: string;
  body?: string;
}
