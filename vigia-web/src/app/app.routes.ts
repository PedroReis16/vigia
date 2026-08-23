import { Routes } from '@angular/router';
import { guestGuard } from '@core/guards';
import { LoginComponent } from './pages/authentication/login/login.component';
import { RegisterComponent } from './pages/authentication/register/register.component';
import { mainRoutes } from './pages/main.routes';

export const routes: Routes = [
  {
    path: '',
    children: mainRoutes,
  },
  {
    path: 'login',
    component: LoginComponent,
    canActivate: [guestGuard],
  },
  {
    path: 'register',
    component: RegisterComponent,
    canActivate: [guestGuard],
  },
  {
    path: '**',
    redirectTo: '',
  },
];
