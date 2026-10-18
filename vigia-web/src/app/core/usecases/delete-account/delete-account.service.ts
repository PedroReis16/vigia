import { HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import {
  AuthSessionService,
  KeycloakAuthService,
  UserProfileHttpService,
  UserProfileStoreService,
} from '@core/services';
import { firstValueFrom } from 'rxjs';
import { LogoutService } from '../logout/logout.service';
import { ProfileUseCaseError } from '../profile-use-case.error';

@Injectable({
  providedIn: 'root',
})
export class DeleteAccountService {
  private readonly profileHttp = inject(UserProfileHttpService);
  private readonly logout = inject(LogoutService);
  private readonly session = inject(AuthSessionService);
  private readonly keycloak = inject(KeycloakAuthService);
  private readonly profileStore = inject(UserProfileStoreService);

  async execute(): Promise<void> {
    try {
      await firstValueFrom(this.profileHttp.deleteAccount());
    } catch (error: unknown) {
      if (isAccountDeleteForbidden(error)) {
        throw new ProfileUseCaseError('PROFILE.DELETE_FORBIDDEN');
      }
      throw new ProfileUseCaseError('PROFILE.DELETE_ERROR');
    }

    try {
      await this.logout.execute();
    } catch {
      this.profileStore.set(null);
      this.session.clearSession();
      this.keycloak.clearToken();
      if (typeof window !== 'undefined') {
        window.location.assign('/');
      }
    }
  }
}

function isAccountDeleteForbidden(error: unknown): boolean {
  if (!(error instanceof HttpErrorResponse) || !error.error || typeof error.error !== 'object') {
    return false;
  }

  const body = error.error as { errorCode?: unknown; ErrorCode?: unknown };
  const code = body.errorCode ?? body.ErrorCode;
  return code === 'ACCOUNT_DELETE_FORBIDDEN' || code === 51;
}
