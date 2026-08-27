import {
  AfterViewInit,
  Component,
  DestroyRef,
  effect,
  inject,
  OnDestroy,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  captureDeviceCardVideoTarget,
  captureDeviceDetailVideoTarget,
  DeviceCardSnapshot,
  DeviceCardThumbTarget,
  DeviceVideoTarget,
  fallbackDeviceDetailVideoTarget,
  fallbackListCardThumbTarget,
} from '@core/helpers/device-card-bounds.helper';
import {
  boundsNearlyEqual,
  easeInOutCubic,
  easeOutCubic,
  ElementBounds,
  lerp,
  lerpBounds,
} from '@core/helpers/element-bounds.helper';
import { DeviceDetailTransitionService } from '@core/services';

const DURATION_MS = 520;
const MOBILE_MAX_WIDTH = '(max-width: 767px)';
const SETTLE_MAX_FRAMES = 24;

@Component({
  selector: 'app-device-detail-transition',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './device-detail-transition.component.html',
  styleUrl: './device-detail-transition.component.css',
})
export class DeviceDetailTransitionComponent implements AfterViewInit, OnDestroy {
  private readonly transition = inject(DeviceDetailTransitionService);
  private readonly destroyRef = inject(DestroyRef);

  private animationFrame = 0;
  private animationStart = 0;
  private viewReady = false;
  private playbackStarted = false;
  private appliedBounds: ElementBounds = { top: 0, left: 0, width: 0, height: 0 };

  readonly bridgeActive = signal(false);
  readonly overlayActive = signal(false);
  readonly thumbVisible = signal(false);
  readonly thumbTop = signal(0);
  readonly thumbLeft = signal(0);
  readonly thumbWidth = signal(0);
  readonly thumbHeight = signal(0);
  readonly thumbRadius = signal(0);
  readonly scrimOpacity = signal(0);
  readonly scrimVisible = signal(false);
  readonly displayName = signal('');
  readonly thumbnailUrl = signal<string | null>(null);
  readonly imageFailed = signal(false);

  constructor() {
    effect(() => {
      this.transition.kind();
      this.transition.snapshot();
      this.transition.readyToPlay();
      if (this.viewReady) {
        this.tryStartAnimation();
      }
    });

    effect(() => {
      const kind = this.transition.kind();
      const snapshot = this.transition.snapshot();
      const ready = this.transition.readyToPlay();

      if (kind === 'exit' && snapshot && !ready && !this.playbackStarted) {
        this.applySnapshot(snapshot);
        this.paintBridge(snapshot);
      }
    });
  }

  ngAfterViewInit(): void {
    this.viewReady = true;
    this.tryStartAnimation();
  }

  ngOnDestroy(): void {
    this.stopAnimation();
  }

  private tryStartAnimation(): void {
    if (this.playbackStarted) {
      return;
    }

    const kind = this.transition.kind();
    const snapshot = this.transition.snapshot();
    if (!snapshot || kind === 'idle' || !this.transition.readyToPlay()) {
      return;
    }

    if (this.prefersReducedMotion()) {
      this.transition.complete();
      return;
    }

    this.playbackStarted = true;
    this.destroyRef.onDestroy(() => this.stopAnimation());
    this.applySnapshot(snapshot);
    this.paintBridge(snapshot);

    if (kind === 'enter') {
      this.startEnterAnimation(snapshot);
      return;
    }

    requestAnimationFrame(() => this.startExitAnimation(snapshot));
  }

  private startEnterAnimation(snapshot: DeviceCardSnapshot): void {
    const isMobile = this.isMobileViewport();
    const target = captureDeviceDetailVideoTarget() ?? fallbackDeviceDetailVideoTarget(isMobile);

    this.overlayActive.set(true);
    this.thumbVisible.set(true);
    this.scrimVisible.set(false);
    this.scrimOpacity.set(0);
    this.applyBounds(snapshot.bounds, snapshot.borderRadius);

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        this.transition.beginPlayback();
        this.bridgeActive.set(false);
        this.animationStart = performance.now();
        this.tickEnter(snapshot.bounds, target, snapshot.borderRadius);
      });
    });
  }

  private startExitAnimation(snapshot: DeviceCardSnapshot): void {
    const cardTarget =
      captureDeviceCardVideoTarget(snapshot.deviceId) ??
      fallbackListCardThumbTarget(snapshot.bounds);

    this.overlayActive.set(true);
    this.thumbVisible.set(true);
    this.scrimVisible.set(false);
    this.scrimOpacity.set(0);
    this.applyBounds(snapshot.bounds, snapshot.borderRadius);

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        this.transition.beginPlayback();
        this.bridgeActive.set(false);
        this.animationStart = performance.now();
        this.tickExit(snapshot.bounds, cardTarget, snapshot.borderRadius);
      });
    });
  }

  private tickEnter(
    start: ElementBounds,
    target: DeviceVideoTarget,
    startRadius: number,
  ): void {
    const elapsed = performance.now() - this.animationStart;
    const rawT = Math.min(elapsed / DURATION_MS, 1);
    const t = easeInOutCubic(rawT);
    const liveTarget = captureDeviceDetailVideoTarget() ?? target;

    if (rawT >= 1) {
      this.applyBounds(liveTarget.bounds, liveTarget.borderRadius);
      this.syncReveal(1);
      void this.finishEnter();
      return;
    }

    if (rawT >= 0.82) {
      const chase = (rawT - 0.82) / 0.18;
      this.applyBounds(
        lerpBounds(this.appliedBounds, liveTarget.bounds, 0.25 + chase * 0.75),
        lerp(this.thumbRadius(), liveTarget.borderRadius, 0.25 + chase * 0.75),
      );
    } else {
      this.applyBounds(
        lerpBounds(start, liveTarget.bounds, t),
        lerp(startRadius, liveTarget.borderRadius, t),
      );
    }

    this.syncReveal(rawT);
    this.scrimOpacity.set(0);

    this.animationFrame = requestAnimationFrame(() =>
      this.tickEnter(start, target, startRadius),
    );
  }

  private tickExit(
    start: ElementBounds,
    target: DeviceCardThumbTarget,
    startRadius: number,
  ): void {
    const elapsed = performance.now() - this.animationStart;
    const rawT = Math.min(elapsed / DURATION_MS, 1);
    const t = easeInOutCubic(rawT);
    const deviceId = this.transition.snapshot()?.deviceId ?? '';
    const liveTarget =
      captureDeviceCardVideoTarget(deviceId) ?? target;

    if (rawT >= 1) {
      this.applyBounds(liveTarget.bounds, liveTarget.borderRadius);
      this.syncReveal(1);
      void this.finishExit();
      return;
    }

    if (rawT >= 0.82) {
      const chase = (rawT - 0.82) / 0.18;
      this.applyBounds(
        lerpBounds(this.appliedBounds, liveTarget.bounds, 0.25 + chase * 0.75),
        lerp(this.thumbRadius(), liveTarget.borderRadius, 0.25 + chase * 0.75),
      );
    } else {
      this.applyBounds(
        lerpBounds(start, liveTarget.bounds, t),
        lerp(startRadius, liveTarget.borderRadius, t),
      );
    }

    this.syncReveal(rawT);
    this.scrimOpacity.set(0);

    this.animationFrame = requestAnimationFrame(() =>
      this.tickExit(start, target, startRadius),
    );
  }

  private async finishEnter(): Promise<void> {
    await this.settleOverlayToTarget();
    this.syncReveal(1);
    await nextFrame();
    await nextFrame();

    this.hideOverlay();
    await nextFrame();

    this.transition.complete();
    this.playbackStarted = false;
  }

  private async finishExit(): Promise<void> {
    await this.settleOverlayToCard();
    this.syncReveal(1);
    await nextFrame();
    await nextFrame();

    this.hideOverlay();
    await nextFrame();

    this.transition.complete();
    this.playbackStarted = false;
  }

  private async settleOverlayToTarget(): Promise<void> {
    let stableFrames = 0;

    for (let frame = 0; frame < SETTLE_MAX_FRAMES; frame += 1) {
      const target = captureDeviceDetailVideoTarget();
      if (!target) {
        await nextFrame();
        continue;
      }

      this.applyBounds(target.bounds, target.borderRadius);

      if (boundsNearlyEqual(this.appliedBounds, target.bounds)) {
        stableFrames += 1;
        if (stableFrames >= STABLE_FRAMES_REQUIRED) {
          return;
        }
      } else {
        stableFrames = 0;
      }

      await nextFrame();
    }
  }

  private async settleOverlayToCard(): Promise<void> {
    const deviceId = this.transition.snapshot()?.deviceId;
    if (!deviceId) {
      return;
    }

    let stableFrames = 0;

    for (let frame = 0; frame < SETTLE_MAX_FRAMES; frame += 1) {
      const target = captureDeviceCardVideoTarget(deviceId);
      if (!target) {
        await nextFrame();
        continue;
      }

      this.applyBounds(target.bounds, target.borderRadius);

      if (boundsNearlyEqual(this.appliedBounds, target.bounds)) {
        stableFrames += 1;
        if (stableFrames >= STABLE_FRAMES_REQUIRED) {
          return;
        }
      } else {
        stableFrames = 0;
      }

      await nextFrame();
    }
  }

  private hideOverlay(): void {
    this.overlayActive.set(false);
    this.bridgeActive.set(false);
    this.thumbVisible.set(false);
    this.scrimVisible.set(false);
    this.scrimOpacity.set(0);
  }

  private paintBridge(snapshot: DeviceCardSnapshot): void {
    this.bridgeActive.set(true);
    this.applyBounds(snapshot.bounds, snapshot.borderRadius);
  }

  private applySnapshot(snapshot: DeviceCardSnapshot): void {
    this.displayName.set(snapshot.displayName);
    this.thumbnailUrl.set(snapshot.thumbnailUrl);
    this.imageFailed.set(snapshot.imageFailed);
  }

  private syncReveal(rawT: number): void {
    const revealProgress = intervalTransform(rawT, 0.04, 1, easeOutCubic);
    this.transition.updateReveal(revealProgress, this.appliedBounds);
  }

  private applyBounds(bounds: ElementBounds, radius: number): void {
    const rounded = {
      top: Math.round(bounds.top),
      left: Math.round(bounds.left),
      width: Math.round(bounds.width),
      height: Math.round(bounds.height),
    };

    this.appliedBounds = rounded;
    this.thumbTop.set(rounded.top);
    this.thumbLeft.set(rounded.left);
    this.thumbWidth.set(rounded.width);
    this.thumbHeight.set(rounded.height);
    this.thumbRadius.set(radius);
  }

  private stopAnimation(): void {
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
      this.animationFrame = 0;
    }
  }

  private isMobileViewport(): boolean {
    return (
      typeof window !== 'undefined' &&
      typeof window.matchMedia === 'function' &&
      window.matchMedia(MOBILE_MAX_WIDTH).matches
    );
  }

  private prefersReducedMotion(): boolean {
    return (
      typeof window !== 'undefined' &&
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    );
  }
}

const STABLE_FRAMES_REQUIRED = 2;

function intervalTransform(
  t: number,
  start: number,
  end: number,
  curve: (value: number) => number,
): number {
  if (t <= start) {
    return 0;
  }
  if (t >= end) {
    return 1;
  }
  return curve((t - start) / (end - start));
}

function nextFrame(): Promise<void> {
  return new Promise((resolve) => {
    requestAnimationFrame(() => resolve());
  });
}
