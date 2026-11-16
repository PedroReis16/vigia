import { inject } from '@angular/core';
import { CanActivateFn } from '@angular/router';
import { AuthSessionService } from '@core/services';
import { BeginKeycloakAuthService } from '@core/usecases';

export const authGuard: CanActivateFn = (_route, state) => {
  const session = inject(AuthSessionService);
  const beginAuth = inject(BeginKeycloakAuthService);

  if (session.isAuthenticated()) {
    return true;
  }

  void beginAuth.execute('login', state.url || '/devices');
  return false;
};
