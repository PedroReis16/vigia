import { DeviceRooms } from '@core/enums';

export interface UpdateDeviceDto {
  nickname?: string | null;
  room?: DeviceRooms | null;
  isClipsEnabled?: boolean | null;
}
