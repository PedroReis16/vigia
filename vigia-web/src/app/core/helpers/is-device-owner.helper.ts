import { Device } from '@core/entities';

export function isDeviceOwner(device: Device, userId: string | null): boolean {
  if (!userId || !device.ownerId) {
    return false;
  }
  return device.ownerId === userId;
}
