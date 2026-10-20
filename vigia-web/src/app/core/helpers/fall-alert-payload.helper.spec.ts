import {
  mapUserNotificationDto,
  parseFallAlertPayload,
  resolveFallAlertDeviceId,
} from './fall-alert-payload.helper';

describe('fall-alert-payload.helper', () => {
  it('parses a valid fall alert payload', () => {
    const result = parseFallAlertPayload(
      {
        type: 'fall',
        deviceId: 'device-1',
        deviceName: 'Vigia-abc',
        nickname: 'Sala',
        alertId: 'episode-1',
      },
      { title: 'Alerta de queda', body: 'Queda detectada em Sala' },
    );

    expect(result).toMatchObject({
      id: 'episode-1',
      episodeId: 'episode-1',
      type: 'fall',
      deviceId: 'device-1',
      deviceName: 'Vigia-abc',
      nickname: 'Sala',
      title: 'Alerta de queda',
      body: 'Queda detectada em Sala',
      read: false,
    });
  });

  it('returns null for non-fall payloads', () => {
    expect(parseFallAlertPayload({ type: 'other', deviceId: 'device-1' })).toBeNull();
  });

  it('returns null when deviceId is missing', () => {
    expect(parseFallAlertPayload({ type: 'fall' })).toBeNull();
  });

  it('resolves deviceId for navigation', () => {
    expect(resolveFallAlertDeviceId({ type: 'fall', deviceId: 'device-1' })).toBe('device-1');
    expect(resolveFallAlertDeviceId({ type: 'device_offline', deviceId: 'device-1' })).toBe(
      'device-1',
    );
    expect(resolveFallAlertDeviceId({ type: 'other', deviceId: 'device-1' })).toBeNull();
  });

  it('parses a device offline payload and keeps the api copy', () => {
    const result = parseFallAlertPayload(
      {
        type: 'device_offline',
        deviceId: 'device-2',
        deviceName: 'Vigia-def',
        nickname: 'Quarto',
        alertId: 'episode-2',
      },
      {
        title: 'Dispositivo parado',
        body: 'O dispositivo Quarto parou de funcionar',
      },
    );

    expect(result).toMatchObject({
      id: 'episode-2',
      type: 'device_offline',
      deviceId: 'device-2',
      title: 'Dispositivo parado',
      body: 'O dispositivo Quarto parou de funcionar',
    });
  });

  it('maps inbox items without forcing the fall type', () => {
    expect(
      mapUserNotificationDto({
        id: 'n-1',
        episodeId: 'episode-2',
        deviceId: 'device-2',
        type: 'device_offline',
        title: 'Dispositivo parado',
        body: 'O dispositivo Quarto parou de funcionar',
        createdAt: '2026-10-15T12:00:00Z',
        read: false,
      }).type,
    ).toBe('device_offline');
  });
});
