import { inject, Injectable } from '@angular/core';
import {
  LogoutResponseDto,
  SessionHttpService,
} from '@core/services/http/session/session-http.service';
import { firstValueFrom } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class LogoutSessionService {
  private readonly sessionHttp = inject(SessionHttpService);

  execute(input: {
    refreshToken: string;
    pushToken?: string | null;
    idToken?: string | null;
    postLogoutRedirectUri?: string | null;
  }): Promise<LogoutResponseDto> {
    return firstValueFrom(
      this.sessionHttp.logout({
        refreshToken: input.refreshToken,
        pushToken: input.pushToken,
        idToken: input.idToken,
        postLogoutRedirectUri: input.postLogoutRedirectUri,
      }),
    );
  }
}
