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
import { AuthUseCaseError, LoginService } from '@core/usecases';
import { MessageService } from '@core/services';
import { InputComponent } from '@shared/components/input/input.component';
import { MessageComponent } from '@shared/components/message/message.component';

@Component({
  selector: 'app-login',
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
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent {
  private readonly login = inject(LoginService);
  private readonly router = inject(Router);
  private readonly messageService = inject(MessageService);
  private readonly translate = inject(TranslateService);

  readonly submitting = signal(false);

  readonly form = new FormGroup({
    email: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required],
    }),
    password: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required],
    }),
  });

  get emailControl(): FormControl<string> {
    return this.form.controls.email;
  }

  get passwordControl(): FormControl<string> {
    return this.form.controls.password;
  }

  async onSubmit(): Promise<void> {
    if (this.form.invalid || this.submitting()) {
      this.form.markAllAsTouched();
      return;
    }

    this.submitting.set(true);
    this.messageService.removeMessage();

    try {
      await this.login.execute(this.form.getRawValue());
      await this.router.navigate(['/devices']);
    } catch (error: unknown) {
      const key =
        error instanceof AuthUseCaseError ? error.message : 'AUTH.ERRORS.LOGIN';
      this.messageService.addMessage({
        type: 'error',
        message: this.translate.instant(key),
      });
    } finally {
      this.submitting.set(false);
    }
  }
}
