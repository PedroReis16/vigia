import { describe, expect, it } from 'vitest';
import { DeviceRooms } from '@core/enums';
import { environment } from '@environments/environment';
import { DeviceMapper } from './devices.mapper';

describe('DeviceMapper', () => {
  it('maps dto fields and resolves relative thumbnail URL', () => {
    const device = DeviceMapper.fromDto({
      id: 'b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c',
      name: 'Vigia-a1b2c3d4',
      nickname: 'Câmera Teste',
      room: 'LivingRoom',
      ownerId: '80eed123-8e77-47a3-8fae-cedb1ab3eef7',
      macAddress: 'AA:BB:CC:DD:EE:FF',
      thumbnailUrl: 'pictures/frame.jpg',
      isRunning: true,
      isClipsEnabled: false,
    });

    expect(device.id).toBe('b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c');
    expect(device.name).toBe('Vigia-a1b2c3d4');
    expect(device.nickname).toBe('Câmera Teste');
    expect(device.displayName).toBe('Câmera Teste');
    expect(device.room).toBe(DeviceRooms.LivingRoom);
    expect(device.isRunning).toBe(true);
    const apiBase = environment.apiUrl.replace(/\/$/, '');
    expect(device.thumbnailUrl).toBe(`${apiBase}/pictures/frame.jpg`);
  });

  it('falls back to name when nickname is empty and leaves room null', () => {
    const device = DeviceMapper.fromDto({
      id: '1',
      name: 'Vigia-deadbeef',
      nickname: '  ',
      room: 'UnknownRoom',
      macAddress: '',
      thumbnailUrl: null,
      isRunning: false,
      isClipsEnabled: false,
    });

    expect(device.displayName).toBe('Vigia-deadbeef');
    expect(device.room).toBeNull();
    expect(device.thumbnailUrl).toBeNull();
  });
});
