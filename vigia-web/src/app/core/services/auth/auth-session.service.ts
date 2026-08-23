import { inject, Injectable } from '@angular/core';
import { AUTH_STORAGE_KEYS } from '@core/constants';
import { readJwtSubject } from '@core/helpers';
import { StorageService } from '@core/services/storage/storage.service';
import { AuthTokensDto } from '@core/entities/DTOs/auth.dto';

@Injectable({
  providedIn: 'root',
})
export class AuthSessionService {
  private readonly storage = inject(StorageService);

  isAuthenticated(): boolean {
    const refreshToken = this.getRefreshToken();
    return !!refreshToken;
  }

  getAccessToken(): string | null {
    return this.storage.getItem(AUTH_STORAGE_KEYS.accessToken);
  }

  getRefreshToken(): string | null {
    return this.storage.getItem(AUTH_STORAGE_KEYS.refreshToken);
  }

  getUserId(): string | null {
    return this.storage.getItem(AUTH_STORAGE_KEYS.userId);
  }

  setSession(tokens: AuthTokensDto): void {
    this.storage.setItem(AUTH_STORAGE_KEYS.accessToken, tokens.accessToken);
    this.storage.setItem(AUTH_STORAGE_KEYS.refreshToken, tokens.refreshToken);

    const userId = readJwtSubject(tokens.accessToken);
    if (userId) {
      this.storage.setItem(AUTH_STORAGE_KEYS.userId, userId);
    } else {
      this.storage.removeItem(AUTH_STORAGE_KEYS.userId);
    }
  }

  clearSession(): void {
    this.storage.removeItem(AUTH_STORAGE_KEYS.accessToken);
    this.storage.removeItem(AUTH_STORAGE_KEYS.refreshToken);
    this.storage.removeItem(AUTH_STORAGE_KEYS.userId);
  }
}
