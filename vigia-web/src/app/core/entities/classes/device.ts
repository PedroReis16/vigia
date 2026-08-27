import { DeviceRooms } from '@core/enums';

export class Device {
  constructor(
    public readonly id: string,
    public readonly name: string,
    public readonly nickname: string | null,
    public readonly ownerId: string | null,
    public readonly macAddress: string,
    public readonly room: DeviceRooms | null,
    public readonly thumbnailUrl: string | null,
    public readonly isRunning: boolean,
    public readonly isClipsEnabled: boolean,
  ) {}

  get displayName(): string {
    return this.nickname?.trim() || this.name;
  }
}
