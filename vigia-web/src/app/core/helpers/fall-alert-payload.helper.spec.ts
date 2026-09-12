import { parseFallAlertPayload, resolveFallAlertDeviceId } from './fall-alert-payload.helper';

describe('fall-alert-payload.helper', () => {
  it('parses a valid fall alert payload', () => {
    const result = parseFallAlertPayload(
      {
        type: 'fall',
        deviceId: 'device-1',
        deviceName: 'Vigia-abc',
        nickname: 'Sala',
      },
      { title: 'Alerta de queda', body: 'Queda detectada em Sala' },
    );

    expect(result).toMatchObject({
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
    expect(resolveFallAlertDeviceId({ type: 'other', deviceId: 'device-1' })).toBeNull();
  });
});
