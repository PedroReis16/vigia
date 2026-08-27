import { Component, computed, DestroyRef, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import {
  AuthToShellTransitionComponent,
  DeviceDetailTransitionComponent,
  MessageComponent,
  ToolbarComponent,
} from '@shared/components';
import {
  AuthExitTransitionService,
  DeviceGroupsRealtimeService,
} from '@core/services';

const DEVICE_DETAIL_ROUTE = /^\/devices\/[^/]+(\/clips)?$/;
const MOBILE_MAX_WIDTH = '(max-width: 767px)';

@Component({
  selector: 'app-layout',
  imports: [
    RouterOutlet,
    ToolbarComponent,
    MessageComponent,
    AuthToShellTransitionComponent,
    DeviceDetailTransitionComponent,
  ],
  standalone: true,
  templateUrl: './layout.component.html',
  styleUrl: './layout.component.css',
})
export class LayoutComponent implements OnInit, OnDestroy {
  private readonly authExitTransition = inject(AuthExitTransitionService);
  private readonly realtime = inject(DeviceGroupsRealtimeService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  readonly isMobileDeviceDetail = signal(false);
  readonly shellTransitionMode = computed(() =>
    this.authExitTransition.kind() === 'logout' ? 'exit' : 'enter',
  );
  readonly logoutMorphActive = computed(
    () =>
      this.authExitTransition.kind() === 'logout' &&
      !this.authExitTransition.settled(),
  );
  readonly enterMorphActive = computed(
    () =>
      (this.authExitTransition.kind() === 'login' ||
        this.authExitTransition.kind() === 'register') &&
      !this.authExitTransition.settled(),
  );

  private mediaQuery: MediaQueryList | null = null;
  private readonly onMediaQueryChange = (): void => {
    this.updateMobileDeviceDetailLayout();
  };

  ngOnInit(): void {
    void this.realtime.connect();
    this.updateMobileDeviceDetailLayout();

    this.router.events
      .pipe(
        filter((event) => event instanceof NavigationEnd),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe(() => this.updateMobileDeviceDetailLayout());

    if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
      this.mediaQuery = window.matchMedia(MOBILE_MAX_WIDTH);
      this.mediaQuery.addEventListener('change', this.onMediaQueryChange);
    }
  }

  ngOnDestroy(): void {
    void this.realtime.disconnect();
    this.mediaQuery?.removeEventListener('change', this.onMediaQueryChange);
  }

  private updateMobileDeviceDetailLayout(): void {
    const path = this.router.url.split('?')[0] ?? '';
    const isDeviceDetail = DEVICE_DETAIL_ROUTE.test(path);
    const isMobile = this.mediaQuery?.matches ?? false;
    this.isMobileDeviceDetail.set(isDeviceDetail && isMobile);
  }
}
