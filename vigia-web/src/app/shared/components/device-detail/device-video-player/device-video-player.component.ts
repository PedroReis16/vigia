import { Component, ElementRef, effect, input, OnDestroy, output, signal, viewChild } from '@angular/core';
import { TranslateModule } from '@ngx-translate/core';
import { ButtonModule } from '@openng/optimus-ui/button';
import { WhepLiveSessionState } from '@core/services';

@Component({
  selector: 'app-device-video-player',
  standalone: true,
  imports: [TranslateModule, ButtonModule],
  templateUrl: './device-video-player.component.html',
  styleUrl: './device-video-player.component.css',
})
export class DeviceVideoPlayerComponent implements OnDestroy {
  readonly sessionState = input.required<WhepLiveSessionState>();
  readonly fullscreen = input(false);

  readonly retry = output<void>();
  readonly toggleFullscreen = output<void>();
  readonly togglePause = output<void>();

  readonly videoRef = viewChild<ElementRef<HTMLVideoElement>>('videoEl');

  readonly showControls = signal(true);
  private hideControlsTimer: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    effect(() => {
      const stream = this.sessionState().remoteStream;
      const video = this.videoRef()?.nativeElement;
      if (!video) {
        return;
      }
      if (video.srcObject !== stream) {
        video.srcObject = stream;
        if (stream) {
          void video.play().catch(() => undefined);
        }
      }
    });
  }

  ngOnDestroy(): void {
    this.clearHideTimer();
  }

  onVideoContainerClick(): void {
    this.showControls.set(!this.showControls());
    this.scheduleHideControls();
  }

  onTogglePause(): void {
    this.togglePause.emit();
    this.scheduleHideControls();
  }

  onToggleFullscreen(): void {
    this.toggleFullscreen.emit();
  }

  onRetry(): void {
    this.retry.emit();
  }

  private scheduleHideControls(): void {
    this.clearHideTimer();
    if (this.sessionState().status === 'playing') {
      this.hideControlsTimer = setTimeout(() => this.showControls.set(false), 3000);
    }
  }

  private clearHideTimer(): void {
    if (this.hideControlsTimer) {
      clearTimeout(this.hideControlsTimer);
      this.hideControlsTimer = null;
    }
  }
}
