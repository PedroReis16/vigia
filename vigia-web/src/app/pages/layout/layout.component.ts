import { Component, computed, inject, OnDestroy, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import {
  AuthToShellTransitionComponent,
  MessageComponent,
  ToolbarComponent,
} from '@shared/components';
import {
  AuthExitTransitionService,
  DeviceGroupsRealtimeService,
} from '@core/services';

@Component({
  selector: 'app-layout',
  imports: [
    RouterOutlet,
    ToolbarComponent,
    MessageComponent,
    AuthToShellTransitionComponent,
  ],
  standalone: true,
  templateUrl: './layout.component.html',
  styleUrl: './layout.component.css',
})
export class LayoutComponent implements OnInit, OnDestroy {
  private readonly authExitTransition = inject(AuthExitTransitionService);
  private readonly realtime = inject(DeviceGroupsRealtimeService);

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

  ngOnInit(): void {
    void this.realtime.connect();
  }

  ngOnDestroy(): void {
    void this.realtime.disconnect();
  }
}
