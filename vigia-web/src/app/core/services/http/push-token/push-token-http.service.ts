import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface UpsertPushTokenRequestDto {
  token: string;
  platform: string;
}

export interface DeletePushTokenRequestDto {
  token: string;
}

@Injectable({
  providedIn: 'root',
})
export class PushTokenHttpService {
  private readonly http = inject(HttpClient);
  private readonly basePath = '/users/push-token';

  upsertToken(token: string, platform: string): Observable<void> {
    const body: UpsertPushTokenRequestDto = { token, platform };
    return this.http.put<void>(this.basePath, body);
  }

  deleteToken(token: string): Observable<void> {
    const body: DeletePushTokenRequestDto = { token };
    return this.http.delete<void>(this.basePath, { body });
  }
}
