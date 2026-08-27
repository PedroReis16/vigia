import {
  AfterViewInit,
  Component,
  DestroyRef,
  effect,
  inject,
  input,
  OnDestroy,
  signal,
} from '@angular/core';
import { AuthExitTransitionService } from '@core/services';
import {
  AuthLogoBounds,
  measureAuthHandoffLayout,
} from '@core/helpers/auth-logo-bounds.helper';

const DURATION_MS = 780;
const TOOLBAR_LOGO_HEIGHT = 56;
const ENTER_VEIL_HIDE_THRESHOLD = 0.98;
const BODY_SCRIM_START = 0.62;
const BODY_SCRIM_END = 0.92;

interface LogoTarget {
  top: number;
  centerX: number;
  height: number;
}

@Component({
  selector: 'app-auth-to-shell-transition',
  standalone: true,
  templateUrl: './auth-to-shell-transition.component.html',
  styleUrl: './auth-to-shell-transition.component.css',
})
export class AuthToShellTransitionComponent implements AfterViewInit, OnDestroy {
  /** `enter` plays login/register morph; `exit` plays logout morph on the shell. */
  readonly mode = input.required<'enter' | 'exit'>();

  private readonly transition = inject(AuthExitTransitionService);
  private readonly destroyRef = inject(DestroyRef);

  private animationFrame = 0;
  private animationStart = 0;
  private viewReady = false;
  private playbackStarted = false;
  private enterBridgeReleased = false;

  readonly overlayActive = signal(false);
  readonly veilVisible = signal(false);
  readonly veilHeight = signal(0);
  readonly logoVisible = signal(false);
  readonly logoTop = signal(0);
  readonly logoLeft = signal(0);
  readonly logoHeight = signal(0);
  readonly bodyScrimAlpha = signal(0);
  readonly bodyScrimTop = signal(0);

  constructor() {
    effect(() => {
      this.transition.kind();
      if (this.viewReady) {
        this.tryStartAnimation();
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
    const mode = this.mode();
    const shouldPlayEnter = mode === 'enter' && (kind === 'login' || kind === 'register');
    const shouldPlayExit = mode === 'exit' && kind === 'logout';

    if (!shouldPlayEnter && !shouldPlayExit) {
      return;
    }

    if (this.prefersReducedMotion()) {
      if (shouldPlayExit) {
        this.transition.notifyShellExitReady();
      } else {
        this.transition.complete();
      }
      return;
    }

    this.playbackStarted = true;
    this.destroyRef.onDestroy(() => this.stopAnimation());

    if (shouldPlayExit) {
      this.prepareExitFrame();
      requestAnimationFrame(() => this.startReverseAnimation());
      return;
    }

    this.prepareEnterFrame();
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        this.startEnterAnimation();
      });
    });
  }

  private prepareEnterFrame(): void {
    const viewportHeight = window.innerHeight;
    const toolbarHeight = this.measureToolbarHeight() ?? TOOLBAR_LOGO_HEIGHT + 24;
    const origin = this.transition.logoOrigin();
    const target = this.measureToolbarLogoTarget();

    this.enterBridgeReleased = false;
    this.overlayActive.set(true);
    this.veilHeight.set(viewportHeight);
    this.veilVisible.set(true);
    this.bodyScrimTop.set(toolbarHeight);
    this.bodyScrimAlpha.set(1);

    if (origin) {
      this.applyFlyingLogo(origin, target, 0);
    } else {
      this.logoVisible.set(false);
    }
  }

  private prepareExitFrame(): void {
    const viewportHeight = window.innerHeight;
    const toolbarHeight =
      this.transition.toolbarHeight() ??
      this.measureToolbarHeight() ??
      TOOLBAR_LOGO_HEIGHT + 24;
    const origin = this.transition.logoOrigin();
    const target = this.measureLogoutLogoTarget(viewportHeight);

    this.overlayActive.set(true);
    this.veilHeight.set(toolbarHeight);
    this.veilVisible.set(true);
    this.bodyScrimTop.set(toolbarHeight);
    this.bodyScrimAlpha.set(0);

    if (origin) {
      this.applyFlyingLogo(origin, target, 0);
    } else {
      this.logoVisible.set(false);
    }
  }

  private startEnterAnimation(): void {
    const origin = this.transition.logoOrigin();
    const target = this.measureToolbarLogoTarget();
    const viewportHeight = window.innerHeight;
    const toolbarHeight = this.measureToolbarHeight() ?? TOOLBAR_LOGO_HEIGHT + 24;

    this.animationStart = performance.now();
    this.tickEnter(origin, target, viewportHeight, toolbarHeight);
  }

  private startReverseAnimation(): void {
    const origin = this.transition.logoOrigin();
    const viewportHeight = window.innerHeight;
    const toolbarHeight =
      this.transition.toolbarHeight() ??
      this.measureToolbarHeight() ??
      TOOLBAR_LOGO_HEIGHT + 24;
    const target = this.measureLogoutLogoTarget(viewportHeight);

    this.animationStart = performance.now();
    this.tickReverse(origin, target, viewportHeight, toolbarHeight);
  }

  private tickEnter(
    origin: AuthLogoBounds | null,
    target: LogoTarget,
    viewportHeight: number,
    toolbarHeight: number,
  ): void {
    if (!this.enterBridgeReleased) {
      this.enterBridgeReleased = true;
      this.transition.beginPlayback();
    }

    const elapsed = performance.now() - this.animationStart;
    const rawT = Math.min(elapsed / DURATION_MS, 1);
    const t = easeInOutCubic(rawT);

    this.veilHeight.set(lerp(viewportHeight, toolbarHeight, t));
    this.applyEnterVeilVisibility(t);

    const scrimProgress = intervalTransform(rawT, BODY_SCRIM_START, BODY_SCRIM_END, easeOutCubic);
    this.bodyScrimAlpha.set(1 - scrimProgress);

    this.updateFlyingLogoEnter(origin, target, t);

    if (rawT >= 1) {
      this.finishEnter();
      return;
    }

    this.animationFrame = requestAnimationFrame(() =>
      this.tickEnter(origin, target, viewportHeight, toolbarHeight),
    );
  }

  private tickReverse(
    origin: AuthLogoBounds | null,
    target: LogoTarget,
    viewportHeight: number,
    toolbarHeight: number,
  ): void {
    const elapsed = performance.now() - this.animationStart;
    const rawT = Math.min(elapsed / DURATION_MS, 1);
    const t = easeInOutCubic(rawT);

    this.veilHeight.set(lerp(toolbarHeight, viewportHeight, t));
    this.veilVisible.set(true);
    this.bodyScrimAlpha.set(0);

    this.updateFlyingLogoExit(origin, target, t);

    if (rawT >= 1) {
      this.finishExit();
      return;
    }

    this.animationFrame = requestAnimationFrame(() =>
      this.tickReverse(origin, target, viewportHeight, toolbarHeight),
    );
  }

  private applyEnterVeilVisibility(t: number): void {
    const showVeil = t < ENTER_VEIL_HIDE_THRESHOLD;
    if (!showVeil) {
      this.transition.revealToolbarLogo();
    }
    this.veilVisible.set(showVeil);
  }

  private updateFlyingLogoEnter(
    start: AuthLogoBounds | null,
    end: LogoTarget,
    t: number,
  ): void {
    if (!start || t >= ENTER_VEIL_HIDE_THRESHOLD) {
      this.logoVisible.set(false);
      return;
    }

    this.applyFlyingLogo(start, end, t);
  }

  private updateFlyingLogoExit(
    start: AuthLogoBounds | null,
    end: LogoTarget,
    t: number,
  ): void {
    if (!start) {
      this.logoVisible.set(false);
      return;
    }

    this.applyFlyingLogo(start, end, t);
  }

  private applyFlyingLogo(
    start: AuthLogoBounds,
    end: LogoTarget,
    t: number,
  ): void {
    const from = toLogoTarget(start);
    const logoH = lerp(from.height, end.height, t);
    const centerX = lerp(from.centerX, end.centerX, t);
    const logoTop = lerp(from.top, end.top, t);

    this.logoVisible.set(true);
    this.logoHeight.set(logoH);
    this.logoLeft.set(centerX - logoH / 2);
    this.logoTop.set(logoTop);
  }

  private finishEnter(): void {
    this.overlayActive.set(false);
    this.veilVisible.set(false);
    this.logoVisible.set(false);
    this.bodyScrimAlpha.set(0);
    this.enterBridgeReleased = false;
    this.playbackStarted = false;
    this.transition.complete();
  }

  private finishExit(): void {
    const viewportHeight = window.innerHeight;
    const target = this.measureLogoutLogoTarget(viewportHeight);

    if (this.logoVisible()) {
      this.transition.setHandoffLogo({
        top: this.logoTop(),
        left: this.logoLeft(),
        height: this.logoHeight(),
      });
    } else {
      this.transition.setHandoffLogo({
        top: target.top,
        left: target.centerX - target.height / 2,
        height: target.height,
      });
    }

    this.veilHeight.set(viewportHeight);
    this.veilVisible.set(true);
    this.logoVisible.set(false);
    this.bodyScrimAlpha.set(0);
    this.transition.activateLogoutBridge();

    requestAnimationFrame(() => {
      this.overlayActive.set(false);
      this.playbackStarted = false;
      this.transition.notifyShellExitReady();
    });
  }

  private stopAnimation(): void {
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
      this.animationFrame = 0;
    }
  }

  private measureToolbarHeight(): number | null {
    const toolbar = document.querySelector('[data-testid="app-toolbar"]');
    if (!(toolbar instanceof HTMLElement)) {
      return null;
    }

    const rect = toolbar.getBoundingClientRect();
    return rect.height > 0 ? rect.height : null;
  }

  private measureToolbarLogoTarget(): LogoTarget {
    const logo = document.querySelector('[data-testid="toolbar-logo"] img');
    if (logo instanceof HTMLElement) {
      const rect = logo.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        return toLogoTarget(rect);
      }
    }

    const toolbar = document.querySelector('[data-testid="app-toolbar"]');
    const toolbarRect = toolbar instanceof HTMLElement
      ? toolbar.getBoundingClientRect()
      : null;
    const toolbarHeight = toolbarRect?.height ?? TOOLBAR_LOGO_HEIGHT + 24;
    const toolbarTop = toolbarRect?.top ?? 0;
    const toolbarLeft = toolbarRect?.left ?? 20;

    return {
      top: toolbarTop + (toolbarHeight - TOOLBAR_LOGO_HEIGHT) / 2,
      centerX: toolbarLeft + TOOLBAR_LOGO_HEIGHT / 2,
      height: TOOLBAR_LOGO_HEIGHT,
    };
  }

  private measureLogoutLogoTarget(viewportHeight: number): LogoTarget {
    const layout = measureAuthHandoffLayout(viewportHeight);

    return {
      top: layout.logoTop,
      centerX: layout.logoCenterX,
      height: layout.logoHeight,
    };
  }

  private prefersReducedMotion(): boolean {
    return (
      typeof window !== 'undefined' &&
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    );
  }
}

function toLogoTarget(bounds: AuthLogoBounds | DOMRect): LogoTarget {
  return {
    top: bounds.top,
    centerX: bounds.left + bounds.width / 2,
    height: bounds.height,
  };
}

function lerp(start: number, end: number, t: number): number {
  return start + (end - start) * t;
}

function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

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
