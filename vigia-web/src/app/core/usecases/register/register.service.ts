import { HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { AuthErrorCode, resolveAuthErrorCode } from '@core/enums';
import { ApiErrorDto, RegisterRequestDto } from '@core/entities/DTOs/auth.dto';
import { AuthSessionService } from '@core/services/auth/auth-session.service';
import { AuthHttpService } from '@core/services/http/auth/auth-http.service';
import { firstValueFrom } from 'rxjs';
import { AuthUseCaseError } from '../auth-use-case.error';

@Injectable({
  providedIn: 'root',
})
export class RegisterService {
  private readonly authHttp = inject(AuthHttpService);
  private readonly session = inject(AuthSessionService);

  async execute(payload: RegisterRequestDto): Promise<void> {
    try {
      const tokens = await firstValueFrom(this.authHttp.register(payload));
      this.session.setSession(tokens);
    } catch (error: unknown) {
      throw this.toAuthError(error);
    }
  }

  private toAuthError(error: unknown): AuthUseCaseError {
    if (error instanceof HttpErrorResponse) {
      const body = error.error as ApiErrorDto | null;
      const code = resolveAuthErrorCode(body?.errorCode);
      const message =
        code === AuthErrorCode.UserEmailAlreadyInUse
          ? 'AUTH.ERRORS.EMAIL_IN_USE'
          : 'AUTH.ERRORS.REGISTER';

      return new AuthUseCaseError(message, code, error.status);
    }

    return new AuthUseCaseError('AUTH.ERRORS.REGISTER', AuthErrorCode.UnknownError);
  }
}
