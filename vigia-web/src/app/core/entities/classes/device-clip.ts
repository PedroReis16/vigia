import { ClipStatus } from '@core/enums';

export class DeviceClip {
  constructor(
    public readonly id: string,
    public readonly deviceId: string,
    public readonly status: ClipStatus,
    public readonly frameCount: number,
    public readonly fps: number,
    public readonly createdAt: Date,
    public readonly thumbnailUrl: string | null = null,
    public readonly playbackUrl: string | null = null,
  ) {}

  get isReady(): boolean {
    return this.status === ClipStatus.Ready;
  }

  get isPending(): boolean {
    return this.status === ClipStatus.Receiving || this.status === ClipStatus.Assembling;
  }

  get statusKey(): string {
    return `DEVICES.CLIPS.STATUS.${this.status}`;
  }

  /** Approximate length as m:ss from the frame count and fps. */
  get durationLabel(): string | null {
    if (this.fps <= 0) {
      return null;
    }

    const total = Math.max(0, Math.round(this.frameCount / this.fps));
    const minutes = Math.floor(total / 60);
    const seconds = total % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }
}
