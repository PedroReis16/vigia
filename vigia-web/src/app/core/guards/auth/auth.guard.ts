import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthSessionService } from '@core/services';

export const authGuard: CanActivateFn = () => {
  const router = inject(Router);
  const session = inject(AuthSessionService);

  if (session.isAuthenticated()) {
    return true;
  }

  return router.createUrlTree(['/login']);
};
