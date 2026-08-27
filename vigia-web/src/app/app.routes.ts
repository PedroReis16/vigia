import { Routes } from '@angular/router';
import { guestGuard } from '@core/guards';
import { AuthComponent } from './pages/authentication/auth/auth.component';
import { mainRoutes } from './pages/main.routes';

export const routes: Routes = [
  {
    path: '',
    children: mainRoutes,
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
