import { Routes } from '@angular/router';
import { authGuard } from '@core/guards';
import { LayoutComponent } from './layout/layout.component';

export const mainRoutes: Routes = [
  {
    path: '',
    component: LayoutComponent,
    canActivate: [authGuard],
    children: [
      {
        path: '',
        redirectTo: 'home',
        pathMatch: 'full',
      },
      {
        path: 'home',
        loadComponent: () => import('@pages/home/home.component').then((m) => m.HomeComponent),
      },
    ],
  },
];
