import { ClipStatus } from '@core/enums';

export interface DeviceClipDto {
  id: string;
  deviceId: string;
  status: ClipStatus | string;
  frameCount: number;
  fps: number;
  createdAt: string;
  thumbnailUrl?: string | null;
  playbackUrl?: string | null;
}
