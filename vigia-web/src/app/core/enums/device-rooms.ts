export enum DeviceRooms {
  Bedroom = 'Bedroom',
  LivingRoom = 'LivingRoom',
  Kitchen = 'Kitchen',
  Bathroom = 'Bathroom',
  Office = 'Office',
  Garage = 'Garage',
  Backyard = 'Backyard',
  Frontyard = 'Frontyard',
}

const DEVICE_ROOM_VALUES = new Set<string>(Object.values(DeviceRooms));

export function parseDeviceRoom(value: string | null | undefined): DeviceRooms | null {
  if (!value || !DEVICE_ROOM_VALUES.has(value)) {
    return null;
  }
  return value as DeviceRooms;
}

export function deviceRoomI18nKey(room: DeviceRooms | null | undefined): string {
  if (!room) {
    return 'DEVICES.ROOMS.NotDefined';
  }
  return `DEVICES.ROOMS.${room}`;
}
