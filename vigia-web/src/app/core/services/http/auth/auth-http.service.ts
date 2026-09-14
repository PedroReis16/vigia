import { HttpClient, HttpHeaders } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import {
  AuthTokensDto,
  LoginRequestDto,
  RefreshTokenRequestDto,
  RegisterRequestDto,
} from '@core/entities/DTOs/auth.dto';

@Injectable({
  providedIn: 'root',
})
export class AuthHttpService {
  private readonly http = inject(HttpClient);
  private readonly basePath = '/auth';

  private readonly skipAuthHeaders = new HttpHeaders({ 'Skip-Auth': 'true' });

  login(body: LoginRequestDto): Observable<AuthTokensDto> {
    return this.http.post<AuthTokensDto>(`${this.basePath}/login`, body, {
      headers: this.skipAuthHeaders,
    });
  }

  register(body: RegisterRequestDto): Observable<AuthTokensDto> {
    return this.http.post<AuthTokensDto>(`${this.basePath}/register`, body, {
      headers: this.skipAuthHeaders,
    });
  }

  refresh(body: RefreshTokenRequestDto): Observable<AuthTokensDto> {
    return this.http.post<AuthTokensDto>(`${this.basePath}/refresh`, body, {
      headers: this.skipAuthHeaders,
    });
  }

  logout(body: RefreshTokenRequestDto): Observable<void> {
    return this.http.post<void>(`${this.basePath}/logout`, body);
  }
}
