import { DeviceRooms } from '@core/enums';

export interface DeviceDto {
  id: string;
  name: string;
  nickname?: string | null;
  room?: DeviceRooms | string | null;
  ownerId?: string | null;
  macAddress: string;
  thumbnailUrl?: string | null;
  isRunning: boolean;
  isClipsEnabled: boolean;
}
