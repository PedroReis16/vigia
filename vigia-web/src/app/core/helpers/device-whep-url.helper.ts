import { environment } from '@environments/environment';

export function deviceStreamUrl(deviceId: string): string {
  return `${environment.streamBaseUrl}/live/${deviceId}`;
}

export function deviceWhepUrl(deviceId: string): string {
  return `${deviceStreamUrl(deviceId)}/whep`;
}
