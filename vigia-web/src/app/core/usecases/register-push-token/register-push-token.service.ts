import { inject, Injectable } from '@angular/core';
import { PushTokenHttpService } from '@core/services/http/push-token/push-token-http.service';
import { firstValueFrom } from 'rxjs';

const WEB_PLATFORM = 'web';

@Injectable({
  providedIn: 'root',
})
export class RegisterPushTokenService {
  private readonly pushTokenHttp = inject(PushTokenHttpService);

  async execute(token: string): Promise<void> {
    if (!token.trim()) {
      return;
    }

    await firstValueFrom(this.pushTokenHttp.upsertToken(token, WEB_PLATFORM));
  }
}
