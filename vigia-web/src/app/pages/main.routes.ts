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
        redirectTo: 'devices',
        pathMatch: 'full',
      },
      {
        path: 'devices',
        loadComponent: () =>
          import('@pages/devices/devices.component').then((m) => m.DevicesComponent),
      },
      {
        path: 'devices/:deviceId/clips',
        loadComponent: () =>
          import('@pages/device-clips/device-clips.component').then((m) => m.DeviceClipsComponent),
      },
      {
        path: 'devices/:deviceId',
        loadComponent: () =>
          import('@pages/device-detail/device-detail.component').then((m) => m.DeviceDetailComponent),
      },
      {
        path: 'home',
        loadComponent: () => import('@pages/home/home.component').then((m) => m.HomeComponent),
      },
    ],
  },
];
