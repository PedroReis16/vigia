import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthSessionService, PendingInviteService } from '@core/services';
import { BeginKeycloakAuthService } from '@core/usecases';

export const inviteEntryGuard: CanActivateFn = (route) => {
  const session = inject(AuthSessionService);
  const pendingInvite = inject(PendingInviteService);
  const beginAuth = inject(BeginKeycloakAuthService);
  const router = inject(Router);

  const token = route.paramMap.get('token');
  if (!token) {
    return router.createUrlTree(['/devices']);
  }

  if (session.isAuthenticated()) {
    return true;
  }

  pendingInvite.setToken(token);
  void beginAuth.execute('login', `/invite/${token}`);
  return false;
};
