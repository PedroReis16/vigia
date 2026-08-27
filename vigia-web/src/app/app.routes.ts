import { Routes } from '@angular/router';
import { guestGuard, inviteEntryGuard } from '@core/guards';
import { AuthComponent } from './pages/authentication/auth/auth.component';
import { mainRoutes } from './pages/main.routes';

export const routes: Routes = [
  {
    path: '',
    children: mainRoutes,
  },
  {
    path: 'invite/:token',
    canActivate: [inviteEntryGuard],
    loadComponent: () =>
      import('@pages/accept-invite/accept-invite.component').then(
        (m) => m.AcceptInviteComponent,
      ),
  },
  {
    path: 'login',
    component: AuthComponent,
    canActivate: [guestGuard],
  },
  {
    path: 'register',
    redirectTo: () => '/login?mode=register',
  },
  {
    path: '**',
    redirectTo: '',
  },
];
