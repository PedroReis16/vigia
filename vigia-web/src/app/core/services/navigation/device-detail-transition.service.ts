import { Injectable, computed, signal } from '@angular/core';
import { DeviceCardSnapshot } from '@core/helpers/device-card-bounds.helper';
import {
  computeEnterRevealClip,
  ElementBounds,
  EnterRevealClip,
} from '@core/helpers/element-bounds.helper';

export type DeviceTransitionKind = 'idle' | 'enter' | 'exit';

const HIDDEN_REVEAL: EnterRevealClip = { cx: 0, cy: 0, rx: 0, ry: 0, opacity: 0 };

@Injectable({ providedIn: 'root' })
export class DeviceDetailTransitionService {
  readonly kind = signal<DeviceTransitionKind>('idle');
  readonly snapshot = signal<DeviceCardSnapshot | null>(null);
  readonly settled = signal(true);
  /** Full-screen bridge to avoid flashes between routes/overlays. */
  readonly bridgeActive = signal(false);
  readonly readyToPlay = signal(false);
  /** 0–1 progress for chrome wave reveal/collapse during enter/exit. */
  readonly revealProgress = signal(0);
  readonly revealClip = signal<EnterRevealClip>(HIDDEN_REVEAL);

  readonly isArmed = computed(() => this.kind() !== 'idle');

  armEnter(snapshot: DeviceCardSnapshot): void {
    this.kind.set('enter');
    this.snapshot.set(snapshot);
    this.bridgeActive.set(true);
    this.readyToPlay.set(false);
    this.settled.set(false);
    this.resetReveal(snapshot.bounds);
  }

  armExit(snapshot: DeviceCardSnapshot): void {
    this.kind.set('exit');
    this.snapshot.set(snapshot);
    this.bridgeActive.set(true);
    this.readyToPlay.set(false);
    this.settled.set(false);
    this.revealProgress.set(1);
    this.revealClip.set(computeEnterRevealClip(snapshot.bounds, 1));
  }

  notifyReady(): void {
    this.readyToPlay.set(true);
  }

  beginPlayback(): void {
    this.bridgeActive.set(false);
  }

  updateReveal(progress: number, videoBounds: ElementBounds): void {
    const clamped = Math.min(Math.max(progress, 0), 1);
    this.revealProgress.set(clamped);
    this.revealClip.set(computeEnterRevealClip(videoBounds, clamped));
  }

  complete(): void {
    this.kind.set('idle');
    this.snapshot.set(null);
    this.bridgeActive.set(false);
    this.readyToPlay.set(false);
    this.settled.set(true);
    this.resetReveal();
  }

  private resetReveal(bounds?: ElementBounds): void {
    this.revealProgress.set(0);
    this.revealClip.set(bounds ? computeEnterRevealClip(bounds, 0) : HIDDEN_REVEAL);
  }
}
