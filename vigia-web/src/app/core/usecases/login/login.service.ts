import { HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { AuthErrorCode, resolveAuthErrorCode } from '@core/enums';
import { ApiErrorDto, LoginRequestDto } from '@core/entities/DTOs/auth.dto';
import { AuthSessionService } from '@core/services/auth/auth-session.service';
import { AuthHttpService } from '@core/services/http/auth/auth-http.service';
import { firstValueFrom } from 'rxjs';
import { AuthUseCaseError } from '../auth-use-case.error';

@Injectable({
  providedIn: 'root',
})
export class LoginService {
  private readonly authHttp = inject(AuthHttpService);
  private readonly session = inject(AuthSessionService);

  async execute(credentials: LoginRequestDto): Promise<void> {
    try {
      const tokens = await firstValueFrom(this.authHttp.login(credentials));
      this.session.setSession(tokens);
    } catch (error: unknown) {
      throw this.toAuthError(error, 'AUTH.ERRORS.LOGIN');
    }
  }

  private toAuthError(error: unknown, fallbackMessage: string): AuthUseCaseError {
    if (error instanceof HttpErrorResponse) {
      if (error.status === 401) {
        return new AuthUseCaseError(
          'AUTH.ERRORS.INVALID_CREDENTIALS',
          AuthErrorCode.UnknownError,
          401,
        );
      }

      const body = error.error as ApiErrorDto | null;
      return new AuthUseCaseError(
        fallbackMessage,
        resolveAuthErrorCode(body?.errorCode),
        error.status,
      );
    }

    return new AuthUseCaseError(fallbackMessage, AuthErrorCode.UnknownError);
  }
}
