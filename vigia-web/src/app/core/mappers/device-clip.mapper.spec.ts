import { describe, expect, it } from 'vitest';
import { ClipStatus } from '@core/enums';
import { environment } from '@environments/environment';
import { DeviceClipMapper } from './device-clip.mapper';

describe('DeviceClipMapper', () => {
  it('maps clip fields and duration', () => {
    const clip = DeviceClipMapper.fromDto({
      id: 'clip-1',
      deviceId: 'device-1',
      status: 'Ready',
      frameCount: 90,
      fps: 30,
      createdAt: '2026-10-06T15:04:00Z',
      thumbnailUrl: 'devices/device-1/clips/clip-1/thumbnail?accessToken=tok',
      playbackUrl: 'devices/device-1/clips/clip-1?accessToken=tok',
    });

    const apiBase = environment.apiUrl.replace(/\/$/, '');
    expect(clip.id).toBe('clip-1');
    expect(clip.deviceId).toBe('device-1');
    expect(clip.status).toBe(ClipStatus.Ready);
    expect(clip.isReady).toBe(true);
    expect(clip.durationLabel).toBe('0:03');
    expect(clip.createdAt.toISOString()).toBe('2026-10-06T15:04:00.000Z');
    expect(clip.thumbnailUrl).toBe(`${apiBase}/devices/device-1/clips/clip-1/thumbnail?accessToken=tok`);
    expect(clip.playbackUrl).toBe(`${apiBase}/devices/device-1/clips/clip-1?accessToken=tok`);
  });

  it('treats an unknown status as failed and omits duration without fps', () => {
    const clip = DeviceClipMapper.fromDto({
      id: 'clip-2',
      deviceId: 'device-1',
      status: 'Unknown',
      frameCount: 10,
      fps: 0,
      createdAt: '2026-10-06T15:04:00Z',
    });

    expect(clip.status).toBe(ClipStatus.Failed);
    expect(clip.isReady).toBe(false);
    expect(clip.isPending).toBe(false);
    expect(clip.durationLabel).toBeNull();
    expect(clip.thumbnailUrl).toBeNull();
    expect(clip.playbackUrl).toBeNull();
  });
});
