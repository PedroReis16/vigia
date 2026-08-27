import { Injectable, computed, signal } from '@angular/core';
import { AuthLogoBounds, HandoffLogoBounds } from '@core/helpers/auth-logo-bounds.helper';

export type AuthTransitionKind = 'idle' | 'login' | 'register' | 'logout';

@Injectable({ providedIn: 'root' })
export class AuthExitTransitionService {
  readonly kind = signal<AuthTransitionKind>('idle');
  readonly logoOrigin = signal<AuthLogoBounds | null>(null);
  readonly toolbarHeight = signal<number | null>(null);
  readonly settled = signal(true);
  /** Toolbar logo visible under the veil (handoff from flying logo). */
  readonly toolbarLogoRevealed = signal(false);
  /** Full-screen bridge to avoid flashes between routes/overlays. */
  readonly bridgeActive = signal(false);
  /** App-level logo kept visible across logout route change. */
  readonly handoffLogo = signal<HandoffLogoBounds | null>(null);
  /** Auth page content revealed after handoff logo aligns. */
  readonly authHandoffReleased = signal(false);

  readonly isArmed = computed(() => this.kind() !== 'idle');
  readonly isLogoutHandoff = computed(
    () => this.bridgeActive() && this.kind() === 'logout',
  );
  readonly showAppHandoffLogo = computed(
    () => this.handoffLogo() !== null && !this.authHandoffReleased(),
  );

  private shellExitResolve: (() => void) | null = null;

  armLogin(logoOrigin: AuthLogoBounds | null): void {
    this.armEnter('login', logoOrigin);
  }

  armRegister(logoOrigin: AuthLogoBounds | null): void {
    this.armEnter('register', logoOrigin);
  }

  armLogout(logoOrigin: AuthLogoBounds | null, toolbarHeight: number | null): void {
    this.kind.set('logout');
    this.logoOrigin.set(logoOrigin);
    this.toolbarHeight.set(toolbarHeight);
    this.toolbarLogoRevealed.set(false);
    this.bridgeActive.set(false);
    this.settled.set(false);
  }

  complete(): void {
    this.kind.set('idle');
    this.logoOrigin.set(null);
    this.toolbarHeight.set(null);
    this.toolbarLogoRevealed.set(false);
    this.bridgeActive.set(false);
    this.handoffLogo.set(null);
    this.authHandoffReleased.set(false);
    this.settled.set(true);
    this.resolveShellExit();
  }

  /** Shell overlay has painted — safe to drop the app-level bridge. */
  beginPlayback(): void {
    this.bridgeActive.set(false);
  }

  /** Keep full-screen primary visible while the shell route is torn down. */
  activateLogoutBridge(): void {
    this.bridgeActive.set(true);
  }

  setHandoffLogo(logo: HandoffLogoBounds): void {
    this.handoffLogo.set(logo);
    this.authHandoffReleased.set(false);
  }

  syncHandoffLogo(logo: HandoffLogoBounds): void {
    this.handoffLogo.set(logo);
  }

  releaseAuthHandoff(): void {
    this.authHandoffReleased.set(true);
    this.handoffLogo.set(null);
  }

  revealToolbarLogo(): void {
    this.toolbarLogoRevealed.set(true);
  }

  waitForShellExit(): Promise<void> {
    if (this.kind() !== 'logout') {
      return Promise.resolve();
    }

    return new Promise((resolve) => {
      this.shellExitResolve = resolve;
    });
  }

  notifyShellExitReady(): void {
    this.resolveShellExit();
  }

  private armEnter(
    kind: Extract<AuthTransitionKind, 'login' | 'register'>,
    logoOrigin: AuthLogoBounds | null,
  ): void {
    this.kind.set(kind);
    this.logoOrigin.set(logoOrigin);
    this.toolbarHeight.set(null);
    this.toolbarLogoRevealed.set(false);
    this.bridgeActive.set(true);
    this.settled.set(false);
  }

  private resolveShellExit(): void {
    this.shellExitResolve?.();
    this.shellExitResolve = null;
  }
}
