import { Component, DestroyRef, effect, ElementRef, inject, OnInit, signal, viewChild } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { ButtonModule } from '@openng/optimus-ui/button';
import { CardModule } from '@openng/optimus-ui/card';
import { Device, DeviceClip } from '@core/entities';
import { GetDeviceClipsService, GetDeviceService } from '@core/usecases';

const CLIP_POLL_MS = 5000;

@Component({
  selector: 'app-device-clips',
  standalone: true,
  imports: [TranslateModule, ButtonModule, CardModule, RouterLink],
  templateUrl: './device-clips.component.html',
  styleUrl: './device-clips.component.css',
})
export class DeviceClipsComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly getDevice = inject(GetDeviceService);
  private readonly getClips = inject(GetDeviceClipsService);
  private readonly translate = inject(TranslateService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly videoRef = viewChild<ElementRef<HTMLVideoElement>>('player');

  readonly device = signal<Device | null>(null);
  readonly clips = signal<DeviceClip[]>([]);
  readonly loading = signal(true);
  readonly error = signal(false);
  readonly playingId = signal<string | null>(null);
  readonly videoUrl = signal<string | null>(null);
  readonly posterUrl = signal<string | null>(null);
  readonly videoError = signal(false);

  deviceId = '';

  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private destroyed = false;
  private readonly playRequest = signal(0);

  constructor() {
    effect(() => {
      const request = this.playRequest();
      const url = this.videoUrl();
      const video = this.videoRef()?.nativeElement;
      if (!request || !url || !video || this.destroyed) {
        return;
      }

      video.load();
      const playback = video.play?.();
      void playback?.catch(() => undefined);
    });
  }

  ngOnInit(): void {
    this.deviceId = this.route.snapshot.paramMap.get('deviceId') ?? '';
    this.destroyRef.onDestroy(() => {
      this.destroyed = true;
      this.clearPoll();
    });
    void this.load();
  }

  onRetry(): void {
    void this.load();
  }

  onVideoError(): void {
    if (this.destroyed) {
      return;
    }

    // load() aborts the request Angular already started; that is not a failed playback.
    if (this.videoRef()?.nativeElement.error?.code === 1) {
      return;
    }

    this.videoError.set(true);
  }

  formatCreatedAt(clip: DeviceClip): string {
    if (Number.isNaN(clip.createdAt.getTime())) {
      return '';
    }

    const locale = this.translate.currentLang || 'pt-BR';
    return new Intl.DateTimeFormat(locale, {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(clip.createdAt);
  }

  play(clip: DeviceClip): void {
    if (!clip.isReady || !clip.playbackUrl) {
      return;
    }

    if (this.playingId() === clip.id && this.videoUrl() === clip.playbackUrl && !this.videoError()) {
      return;
    }

    this.playingId.set(clip.id);
    this.videoError.set(false);
    this.posterUrl.set(clip.thumbnailUrl);
    this.videoUrl.set(clip.playbackUrl);
    this.playRequest.update((value) => value + 1);
  }

  private async load(silent = false): Promise<void> {
    if (!silent) {
      this.loading.set(true);
      this.error.set(false);
    }

    try {
      const [device, clips] = await Promise.all([
        this.getDevice.execute(this.deviceId),
        this.getClips.execute(this.deviceId),
      ]);
      if (this.destroyed) {
        return;
      }
      this.device.set(device);
      this.clips.set(clips);
      this.error.set(false);
      this.syncPoll(clips);
    } catch {
      if (this.destroyed || silent) {
        return;
      }
      this.error.set(true);
    } finally {
      if (!silent && !this.destroyed) {
        this.loading.set(false);
      }
    }
  }

  private syncPoll(clips: DeviceClip[]): void {
    if (!clips.some((clip) => clip.isPending)) {
      this.clearPoll();
      return;
    }

    if (this.pollTimer != null) {
      return;
    }

    this.pollTimer = setInterval(() => {
      void this.load(true);
    }, CLIP_POLL_MS);
  }

  private clearPoll(): void {
    if (this.pollTimer == null) {
      return;
    }
    clearInterval(this.pollTimer);
    this.pollTimer = null;
  }
}
