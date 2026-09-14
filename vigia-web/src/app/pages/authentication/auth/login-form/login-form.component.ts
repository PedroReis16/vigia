import {
  Component,
  DestroyRef,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { Router } from '@angular/router';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { merge, startWith } from 'rxjs';
import { AuthUseCaseError, LoginService } from '@core/usecases';
import { AuthErrorCode } from '@core/enums';
import { captureAuthLogoBounds } from '@core/helpers';
import {
  AuthExitTransitionService,
  AuthSessionService,
  MessageService,
  PendingInviteService,
} from '@core/services';
import { EMAIL_PATTERN } from '../auth.validators';
import { AuthFloatFieldComponent } from '../float-field/auth-float-field.component';

const WELCOME_HOLD_MS = 800;

@Component({
  selector: 'app-login-form',
  standalone: true,
  imports: [ReactiveFormsModule, TranslateModule, AuthFloatFieldComponent],
  templateUrl: './login-form.component.html',
  styleUrl: '../auth-form-shared.css',
})
export class LoginFormComponent implements OnInit {
  private readonly login = inject(LoginService);
  private readonly authExitTransition = inject(AuthExitTransitionService);
  private readonly session = inject(AuthSessionService);
  private readonly router = inject(Router);
  private readonly messageService = inject(MessageService);
  private readonly translate = inject(TranslateService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly pendingInvite = inject(PendingInviteService);

  readonly submitting = signal(false);
  readonly showWelcome = signal(false);
  /** Mirrors Flutter login: enable when email and password are non-empty. */
  readonly canSubmit = signal(false);

  readonly form = new FormGroup({
    email: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.pattern(EMAIL_PATTERN)],
    }),
    password: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required],
    }),
  });

  readonly ctaActive = computed(
    () => this.canSubmit() || this.showWelcome(),
  );

  readonly ctaDisabled = computed(
    () => !this.canSubmit() || this.submitting() || this.showWelcome(),
  );

  get emailControl(): FormControl<string> {
    return this.form.controls.email;
  }

  get passwordControl(): FormControl<string> {
    return this.form.controls.password;
  }

  get ctaLabel(): string {
    if (this.showWelcome()) {
      return this.translate.instant('AUTH.WELCOME');
    }
    return this.translate.instant('AUTH.LOGIN.SUBMIT');
  }

  ngOnInit(): void {
    merge(this.emailControl.valueChanges, this.passwordControl.valueChanges)
      .pipe(startWith(null), takeUntilDestroyed(this.destroyRef))
      .subscribe(() => this.syncCanSubmit());
  }

  async onSubmit(): Promise<void> {
    this.syncControlsFromDom();
    this.form.markAllAsTouched();
    this.syncCanSubmit();

    if (!this.canSubmit() || this.submitting() || this.showWelcome()) {
      return;
    }

    this.submitting.set(true);
    this.messageService.removeMessage();

    try {
      await this.login.execute(this.form.getRawValue());

      if (!this.session.isAuthenticated()) {
        throw new AuthUseCaseError(
          'AUTH.ERRORS.LOGIN',
          AuthErrorCode.UnknownError,
        );
      }

      this.showWelcome.set(true);
      await this.delay(WELCOME_HOLD_MS);
      this.authExitTransition.armLogin(captureAuthLogoBounds());
      await this.router.navigateByUrl(this.pendingInvite.getPostAuthPath());
    } catch (error: unknown) {
      this.showWelcome.set(false);
      const key =
        error instanceof AuthUseCaseError ? error.message : 'AUTH.ERRORS.LOGIN';
      this.messageService.addMessage({
        type: 'error',
        message: this.translate.instant(key),
      });
      this.submitting.set(false);
    }
  }

  private syncControlsFromDom(): void {
    const email = (
      document.getElementById('login-email') as HTMLInputElement | null
    )?.value;
    const password = (
      document.getElementById('login-password') as HTMLInputElement | null
    )?.value;

    if (typeof email === 'string' && email !== this.emailControl.value) {
      this.emailControl.setValue(email);
    }
    if (typeof password === 'string' && password !== this.passwordControl.value) {
      this.passwordControl.setValue(password);
    }
  }

  private syncCanSubmit(): void {
    const email = this.emailControl.value.trim();
    const password = this.passwordControl.value;
    this.canSubmit.set(email.length > 0 && password.length > 0);
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
