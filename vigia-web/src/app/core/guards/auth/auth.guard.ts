import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { Oauth2Service } from '@core/services';

export const authGuard: CanActivateFn = async () => {
  const router = inject(Router);
  const authService = inject(Oauth2Service);
  const isLoggedIn = await authService.isLoggedIn();

  if (isLoggedIn) {
    return true;
  }

  return router.createUrlTree(['/login']);
};
