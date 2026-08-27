import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthSessionService, PendingInviteService } from '@core/services';

export const inviteEntryGuard: CanActivateFn = (route) => {
  const session = inject(AuthSessionService);
  const pendingInvite = inject(PendingInviteService);
  const router = inject(Router);

  const token = route.paramMap.get('token');
  if (!token) {
    return router.createUrlTree(['/devices']);
  }

  if (session.isAuthenticated()) {
    return true;
  }

  pendingInvite.setToken(token);
  return router.createUrlTree(['/login']);
};
