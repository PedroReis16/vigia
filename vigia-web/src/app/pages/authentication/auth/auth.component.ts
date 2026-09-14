import {
  AfterViewInit,
  Component,
  DestroyRef,
  ElementRef,
  OnInit,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { AuthExitTransitionService } from '@core/services';
import {
  AUTH_PANEL_ESTIMATED_HEIGHT,
  measureAuthHandoffLayout,
} from '@core/helpers/auth-logo-bounds.helper';
import { MessageComponent } from '@shared/components/message/message.component';
import { LoginFormComponent } from './login-form/login-form.component';
import { RegisterFormComponent } from './register-form/register-form.component';

export type AuthMode = 'login' | 'register';

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [
    TranslateModule,
    MessageComponent,
    LoginFormComponent,
    RegisterFormComponent,
  ],
  templateUrl: './auth.component.html',
  styleUrl: './auth.component.css',
})
export class AuthComponent implements OnInit, AfterViewInit {
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);
  private readonly authExitTransition = inject(AuthExitTransitionService);

  private readonly loginPanel =
    viewChild<ElementRef<HTMLElement>>('loginPanel');
  private readonly registerPanel =
    viewChild<ElementRef<HTMLElement>>('registerPanel');

  readonly mode = signal<AuthMode>('login');
  readonly introReady = signal(false);
  readonly panelHeight = signal<number | null>(null);
  readonly logoutHandoff = this.authExitTransition.isLogoutHandoff;
  readonly authHandoffReleased = this.authExitTransition.authHandoffReleased;

  private resizeObserver?: ResizeObserver;
  private handoffPanelLocked = false;

  ngOnInit(): void {
    const initialMode = this.route.snapshot?.queryParamMap?.get('mode');
    if (initialMode === 'register') {
      this.mode.set('register');
    }

    this.route.queryParamMap
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((params) => {
        if (params.get('mode') === 'register') {
          this.mode.set('register');
          queueMicrotask(() => this.syncPanelHeight());
        }
      });

    if (this.logoutHandoff()) {
      this.panelHeight.set(AUTH_PANEL_ESTIMATED_HEIGHT);
      return;
    }

    requestAnimationFrame(() => {
      this.introReady.set(true);
    });
  }

  ngAfterViewInit(): void {
    if (typeof ResizeObserver !== 'undefined') {
      this.resizeObserver = new ResizeObserver(() => this.syncPanelHeight());
      const loginEl = this.loginPanel()?.nativeElement;
      const registerEl = this.registerPanel()?.nativeElement;
      if (loginEl) {
        this.resizeObserver.observe(loginEl);
      }
      if (registerEl) {
        this.resizeObserver.observe(registerEl);
      }
      this.destroyRef.onDestroy(() => this.resizeObserver?.disconnect());
    }

    queueMicrotask(() => {
      this.syncPanelHeight();
      if (this.logoutHandoff()) {
        this.finishLogoutHandoff();
      }
    });
  }

  setMode(mode: AuthMode): void {
    if (this.mode() === mode) {
      return;
    }
    this.mode.set(mode);
    requestAnimationFrame(() => this.syncPanelHeight());
  }

  private finishLogoutHandoff(): void {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        void this.waitForHandoffLayout().then(() => {
          this.syncHandoffLogoToPage();
          requestAnimationFrame(() => {
            this.authExitTransition.releaseAuthHandoff();
            requestAnimationFrame(() => {
              this.introReady.set(true);
              requestAnimationFrame(() => {
                this.handoffPanelLocked = false;
                this.authExitTransition.complete();
              });
            });
          });
        });
      });
    });
  }

  /** Ensures the full auth column is in layout before logo sync / form fade-in. */
  private waitForHandoffLayout(): Promise<void> {
    return new Promise((resolve) => {
      let attempts = 0;

      const tryMeasure = (): void => {
        this.syncPanelHeight();
        const loginEl = this.loginPanel()?.nativeElement;
        const loginHeight =
          loginEl instanceof HTMLElement
            ? loginEl.getBoundingClientRect().height
            : 0;
        const panelReady =
          this.panelHeight() !== null &&
          this.panelHeight()! > 80 &&
          loginHeight > 0;

        if (panelReady || attempts >= 24) {
          this.lockHandoffPanelHeight();
          requestAnimationFrame(() => resolve());
          return;
        }

        attempts += 1;
        requestAnimationFrame(tryMeasure);
      };

      tryMeasure();
    });
  }

  private lockHandoffPanelHeight(): void {
    const loginEl = this.loginPanel()?.nativeElement;
    const registerEl = this.registerPanel()?.nativeElement;
    if (!loginEl || !registerEl) {
      return;
    }

    const loginHeight = Math.ceil(loginEl.getBoundingClientRect().height);
    const registerHeight = Math.ceil(registerEl.getBoundingClientRect().height);
    const next = Math.max(loginHeight, registerHeight, AUTH_PANEL_ESTIMATED_HEIGHT);
    if (next > 0) {
      this.panelHeight.set(next);
      this.handoffPanelLocked = true;
    }
  }

  private syncHandoffLogoToPage(): void {
    const authLogo = document.querySelector('[data-testid="auth-logo"]');
    if (!(authLogo instanceof HTMLElement)) {
      return;
    }

    const rect = authLogo.getBoundingClientRect();
    if (rect.height <= 0) {
      return;
    }

    this.authExitTransition.syncHandoffLogo({
      top: rect.top,
      left: rect.left,
      height: rect.height,
    });
  }

  private syncPanelHeight(): void {
    if (this.handoffPanelLocked) {
      return;
    }

    const loginEl = this.loginPanel()?.nativeElement;
    const registerEl = this.registerPanel()?.nativeElement;
    if (!loginEl || !registerEl) {
      return;
    }

    const loginHeight = Math.ceil(loginEl.getBoundingClientRect().height);
    const registerHeight = Math.ceil(registerEl.getBoundingClientRect().height);
    const next = Math.max(loginHeight, registerHeight);
    if (next > 0) {
      this.panelHeight.set(next);
    }
  }
}
