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
import { AuthUseCaseError, RegisterService } from '@core/usecases';
import { AuthErrorCode } from '@core/enums';
import { captureAuthLogoBounds } from '@core/helpers';
import {
  AuthExitTransitionService,
  AuthSessionService,
  MessageService,
  PendingInviteService,
} from '@core/services';
import {
  EMAIL_PATTERN,
  passwordsMatchValidator,
  requiredTrimmed,
} from '../auth.validators';
import { AuthFloatFieldComponent } from '../float-field/auth-float-field.component';

const WELCOME_HOLD_MS = 800;

@Component({
  selector: 'app-register-form',
  standalone: true,
  imports: [ReactiveFormsModule, TranslateModule, AuthFloatFieldComponent],
  templateUrl: './register-form.component.html',
  styleUrl: '../auth-form-shared.css',
})
export class RegisterFormComponent implements OnInit {
  private readonly register = inject(RegisterService);
  private readonly authExitTransition = inject(AuthExitTransitionService);
  private readonly session = inject(AuthSessionService);
  private readonly router = inject(Router);
  private readonly messageService = inject(MessageService);
  private readonly translate = inject(TranslateService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly pendingInvite = inject(PendingInviteService);

  readonly submitting = signal(false);
  readonly showWelcome = signal(false);
  /** Mirrors Flutter register enable rules. */
  readonly canSubmit = signal(false);

  readonly form = new FormGroup(
    {
      name: new FormControl('', {
        nonNullable: true,
        validators: [requiredTrimmed()],
      }),
      email: new FormControl('', {
        nonNullable: true,
        validators: [Validators.required, Validators.pattern(EMAIL_PATTERN)],
      }),
      password: new FormControl('', {
        nonNullable: true,
        validators: [Validators.required, Validators.minLength(8)],
      }),
      confirmPassword: new FormControl('', {
        nonNullable: true,
        validators: [Validators.required],
      }),
    },
    { validators: [passwordsMatchValidator()] },
  );

  readonly ctaActive = computed(
    () => this.canSubmit() || this.showWelcome(),
  );

  readonly ctaDisabled = computed(
    () => !this.canSubmit() || this.submitting() || this.showWelcome(),
  );

  get nameControl(): FormControl<string> {
    return this.form.controls.name;
  }

  get emailControl(): FormControl<string> {
    return this.form.controls.email;
  }

  get passwordControl(): FormControl<string> {
    return this.form.controls.password;
  }

  get confirmPasswordControl(): FormControl<string> {
    return this.form.controls.confirmPassword;
  }

  get ctaLabel(): string {
    if (this.showWelcome()) {
      return this.translate.instant('AUTH.WELCOME');
    }
    return this.translate.instant('AUTH.REGISTER.SUBMIT');
  }

  ngOnInit(): void {
    merge(
      this.nameControl.valueChanges,
      this.emailControl.valueChanges,
      this.passwordControl.valueChanges,
      this.confirmPasswordControl.valueChanges,
    )
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

    const { name, email, password } = this.form.getRawValue();

    try {
      await this.register.execute({
        name: name.trim(),
        email,
        password,
      });

      if (!this.session.isAuthenticated()) {
        throw new AuthUseCaseError(
          'AUTH.ERRORS.REGISTER',
          AuthErrorCode.UnknownError,
        );
      }

      this.showWelcome.set(true);
      await this.delay(WELCOME_HOLD_MS);
      this.authExitTransition.armRegister(captureAuthLogoBounds());
      await this.router.navigateByUrl(this.pendingInvite.getPostAuthPath());
    } catch (error: unknown) {
      this.showWelcome.set(false);
      const key =
        error instanceof AuthUseCaseError
          ? error.message
          : 'AUTH.ERRORS.REGISTER';
      this.messageService.addMessage({
        type: 'error',
        message: this.translate.instant(key),
      });
      this.submitting.set(false);
    }
  }

  private syncControlsFromDom(): void {
    const fields: Array<[string, FormControl<string>]> = [
      ['register-name', this.nameControl],
      ['register-email', this.emailControl],
      ['register-password', this.passwordControl],
      ['register-confirm-password', this.confirmPasswordControl],
    ];

    for (const [id, control] of fields) {
      const value = (document.getElementById(id) as HTMLInputElement | null)
        ?.value;
      if (typeof value === 'string' && value !== control.value) {
        control.setValue(value);
      }
    }
  }

  private syncCanSubmit(): void {
    const name = this.nameControl.value.trim();
    const email = this.emailControl.value.trim();
    const password = this.passwordControl.value;
    const confirm = this.confirmPasswordControl.value;
    const emailOk = EMAIL_PATTERN.test(email);
    const passwordOk = password.length >= 8;
    const confirmOk = confirm.length > 0 && confirm === password;

    this.canSubmit.set(
      name.length > 0 && emailOk && passwordOk && confirmOk,
    );
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
