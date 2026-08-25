import {
  Component,
  DestroyRef,
  ElementRef,
  inject,
  OnDestroy,
  OnInit,
  signal,
  viewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { ButtonModule } from '@openng/optimus-ui/button';
import { Device, DeviceUser } from '@core/entities';
import { deviceWhepUrl } from '@core/helpers';
import {
  DeviceGroupsRealtimeService,
  WhepLiveSession,
  WhepLiveSessionState,
} from '@core/services';
import {
  GetDeviceService,
  GetDeviceUsersService,
  StartDeviceStreamingService,
  DevicesUseCaseError,
} from '@core/usecases';
import { AuthSessionService } from '@core/services';
import { DeviceDetailsPanelComponent } from '@shared/components/device-detail/device-details-panel/device-details-panel.component';
import { DeviceVideoPlayerComponent } from '@shared/components/device-detail/device-video-player/device-video-player.component';

type DetailViewState = 'loading' | 'ready' | 'error' | 'not_found';

@Component({
  selector: 'app-device-detail',
  standalone: true,
  imports: [
    TranslateModule,
    ButtonModule,
    RouterLink,
    DeviceVideoPlayerComponent,
    DeviceDetailsPanelComponent,
  ],
  templateUrl: './device-detail.component.html',
  styleUrl: './device-detail.component.css',
})
export class DeviceDetailComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly getDevice = inject(GetDeviceService);
  private readonly getDeviceUsers = inject(GetDeviceUsersService);
  private readonly startStreaming = inject(StartDeviceStreamingService);
  private readonly realtime = inject(DeviceGroupsRealtimeService);
  private readonly authSession = inject(AuthSessionService);
  private readonly destroyRef = inject(DestroyRef);

  readonly pageRef = viewChild<ElementRef<HTMLElement>>('pageRoot');

  readonly state = signal<DetailViewState>('loading');
  readonly device = signal<Device | null>(null);
  readonly users = signal<DeviceUser[]>([]);
  readonly usersLoading = signal(false);
  readonly usersError = signal(false);
  readonly sessionState = signal<WhepLiveSessionState>({
    status: 'connecting',
    errorMessage: null,
    isPaused: false,
    isClosed: false,
    remoteStream: null,
  });
  readonly fullscreen = signal(false);
  readonly videoCollapsed = signal(false);

  private session: WhepLiveSession | null = null;
  private unsubscribeSession: (() => void) | null = null;
  private startingLive = false;
  private deviceId = '';

  ngOnInit(): void {
    this.deviceId = this.route.snapshot.paramMap.get('deviceId') ?? '';
    void this.loadDevice();
    void this.loadUsers();
    this.setupRealtime();

    if (typeof document !== 'undefined') {
      document.addEventListener('fullscreenchange', this.onFullscreenChange);
    }
  }

  ngOnDestroy(): void {
    if (typeof document !== 'undefined') {
      document.removeEventListener('fullscreenchange', this.onFullscreenChange);
    }
    void this.teardownSession();
  }

  async loadDevice(): Promise<void> {
    this.state.set('loading');
    try {
      const device = await this.getDevice.execute(this.deviceId);
      this.device.set(device);
      this.state.set('ready');
      void this.startLive();
    } catch (error: unknown) {
      if (error instanceof DevicesUseCaseError && error.message === 'DEVICES.ERRORS.NOT_FOUND') {
        this.state.set('not_found');
        return;
      }
      this.state.set('error');
    }
  }

  async loadUsers(): Promise<void> {
    this.usersLoading.set(true);
    this.usersError.set(false);
    try {
      const users = await this.getDeviceUsers.execute(this.deviceId);
      this.users.set(users);
    } catch {
      this.usersError.set(true);
    } finally {
      this.usersLoading.set(false);
    }
  }

  onBack(): void {
    if (this.fullscreen()) {
      void this.exitFullscreen();
      return;
    }
    void this.leave();
  }

  async onRetryLive(): Promise<void> {
    await this.startLive();
  }

  onTogglePause(): void {
    this.session?.togglePause();
  }

  async onToggleFullscreen(): Promise<void> {
    if (this.fullscreen()) {
      await this.exitFullscreen();
    } else {
      await this.enterFullscreen();
    }
  }

  onDeviceUpdated(device: Device): void {
    this.device.set(device);
  }

  onUsersChanged(): void {
    void this.loadUsers();
  }

  onLeftGroup(): void {
    void this.leave('/devices');
  }

  private setupRealtime(): void {
    this.realtime.membershipChanged$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((event) => {
        if (!event.deviceIds.includes(this.deviceId)) {
          return;
        }

        const currentUserId = this.authSession.getUserId();
        if (event.changeType === 'removed' && event.affectedUserId === currentUserId) {
          void this.leave('/devices');
          return;
        }

        void this.loadDevice();
        void this.loadUsers();
      });
  }

  private async startLive(): Promise<void> {
    if (this.startingLive) {
      return;
    }
    this.startingLive = true;

    await this.teardownSession();
    this.session = new WhepLiveSession(deviceWhepUrl(this.deviceId));
    this.unsubscribeSession = this.session.subscribe((state) => {
      this.sessionState.set(state);
    });

    this.session.beginConnecting();

    try {
      await this.startStreaming.execute(this.deviceId);
      await this.session.connect();
    } catch (error) {
      this.session.markError(error);
    } finally {
      this.startingLive = false;
    }
  }

  private async teardownSession(): Promise<void> {
    this.unsubscribeSession?.();
    this.unsubscribeSession = null;
    if (this.session) {
      await this.session.close();
      this.session = null;
    }
  }

  private async leave(redirectTo = '/devices'): Promise<void> {
    await this.teardownSession();
    await this.router.navigateByUrl(redirectTo);
  }

  private async enterFullscreen(): Promise<void> {
    const root = this.pageRef()?.nativeElement;
    if (!root?.requestFullscreen) {
      this.fullscreen.set(true);
      return;
    }
    await root.requestFullscreen();
    this.fullscreen.set(true);
  }

  private async exitFullscreen(): Promise<void> {
    if (document.fullscreenElement) {
      await document.exitFullscreen();
    }
    this.fullscreen.set(false);
  }

  private onFullscreenChange = (): void => {
    this.fullscreen.set(!!document.fullscreenElement);
  };
}
