import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface LogoutRequestDto {
  refreshToken: string;
  pushToken?: string | null;
  idToken?: string | null;
  postLogoutRedirectUri?: string | null;
}

export interface LogoutResponseDto {
  endSessionUrl: string | null;
}

@Injectable({
  providedIn: 'root',
})
export class SessionHttpService {
  private readonly http = inject(HttpClient);
  private readonly basePath = '/users';

  logout(body: LogoutRequestDto): Observable<LogoutResponseDto> {
    return this.http.post<LogoutResponseDto>(`${this.basePath}/logout`, body);
  }
}
