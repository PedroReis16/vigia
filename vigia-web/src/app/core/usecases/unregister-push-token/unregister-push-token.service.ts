import { inject, Injectable } from '@angular/core';
import { PushTokenHttpService } from '@core/services/http/push-token/push-token-http.service';
import { firstValueFrom } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class UnregisterPushTokenService {
  private readonly pushTokenHttp = inject(PushTokenHttpService);

  async execute(token: string | null | undefined): Promise<void> {
    if (!token?.trim()) {
      return;
    }

    try {
      await firstValueFrom(this.pushTokenHttp.deleteToken(token));
    } catch {
      // Best-effort cleanup on logout.
    }
  }
}
