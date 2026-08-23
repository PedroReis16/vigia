import { Routes } from '@angular/router';
import { LoginComponent, CallbackComponent, mainRoutes } from '@pages';

export const routes: Routes = [
  {
    path: '',
    children: mainRoutes,
  },
  {
    path: 'login',
    component: LoginComponent,
  },
  {
    path: 'callback',
    component: CallbackComponent,
  },
  {
    path: '**',
    redirectTo: '',
  },
];
