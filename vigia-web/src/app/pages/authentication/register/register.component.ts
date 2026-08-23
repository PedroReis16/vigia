import { Component, inject, signal } from '@angular/core';
import {
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { ButtonModule } from '@openng/optimus-ui/button';
import { CardModule } from '@openng/optimus-ui/card';
import { AuthUseCaseError, RegisterService } from '@core/usecases';
import { MessageService } from '@core/services';
import { InputComponent } from '@shared/components/input/input.component';
import { MessageComponent } from '@shared/components/message/message.component';
import {
  EMAIL_PATTERN,
  passwordsMatchValidator,
  requiredTrimmed,
} from './register.validators';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    TranslateModule,
    ButtonModule,
    CardModule,
    RouterLink,
    InputComponent,
    MessageComponent,
  ],
  templateUrl: './register.component.html',
  styleUrl: './register.component.css',
})
export class RegisterComponent {
  private readonly register = inject(RegisterService);
  private readonly router = inject(Router);
  private readonly messageService = inject(MessageService);
  private readonly translate = inject(TranslateService);

  readonly submitting = signal(false);

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

  async onSubmit(): Promise<void> {
    if (this.form.invalid || this.submitting()) {
      this.form.markAllAsTouched();
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
      await this.router.navigate(['/home']);
    } catch (error: unknown) {
      const key =
        error instanceof AuthUseCaseError ? error.message : 'AUTH.ERRORS.REGISTER';
      this.messageService.addMessage({
        type: 'error',
        message: this.translate.instant(key),
      });
    } finally {
      this.submitting.set(false);
    }
  }
}
