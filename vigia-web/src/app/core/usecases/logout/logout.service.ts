import { inject, Injectable } from '@angular/core';
import { AuthSessionService } from '@core/services/auth/auth-session.service';
import { AuthHttpService } from '@core/services/http/auth/auth-http.service';
import { firstValueFrom } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class LogoutService {
  private readonly authHttp = inject(AuthHttpService);
  private readonly session = inject(AuthSessionService);

  async execute(): Promise<void> {
    const refreshToken = this.session.getRefreshToken();

    if (refreshToken) {
      try {
        await firstValueFrom(this.authHttp.logout({ refreshToken }));
      } catch {
        // Best-effort server revoke; local session is cleared regardless.
      }
    }

    this.session.clearSession();
  }
}
