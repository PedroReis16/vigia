import {
  AfterViewInit,
  Component,
  computed,
  DestroyRef,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { TranslateModule } from '@ngx-translate/core';
import { ButtonModule } from '@openng/optimus-ui/button';
import { Device } from '@core/entities/classes/device';
import { waitForDeviceCardThumbBounds } from '@core/helpers/device-card-bounds.helper';
import { DeviceDetailTransitionService, DeviceGroupsRealtimeService } from '@core/services';
import { GetDevicesService } from '@core/usecases';
import { DeviceCardComponent } from '@shared/components/device-card/device-card.component';

type DevicesViewState = 'loading' | 'ready' | 'empty' | 'error';

@Component({
  selector: 'app-devices',
  standalone: true,
  imports: [TranslateModule, ButtonModule, DeviceCardComponent],
  templateUrl: './devices.component.html',
  styleUrl: './devices.component.css',
})
export class DevicesComponent implements OnInit, AfterViewInit {
  private readonly getDevices = inject(GetDevicesService);
  private readonly realtime = inject(DeviceGroupsRealtimeService);
  private readonly transition = inject(DeviceDetailTransitionService);
  private readonly destroyRef = inject(DestroyRef);

  readonly state = signal<DevicesViewState>('loading');
  readonly devices = signal<Device[]>([]);
  readonly skeletonSlots = [0, 1, 2];

  readonly exitPending = computed(
    () => this.transition.kind() === 'exit' && !this.transition.settled(),
  );

  readonly revealClip = computed(() => this.transition.revealClip());

  readonly revealProgress = computed(() => this.transition.revealProgress());

  ngOnInit(): void {
    void this.loadDevices();
    this.realtime.membershipChanged$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        void this.loadDevices();
      });
  }

  ngAfterViewInit(): void {
    if (this.transition.kind() !== 'exit') {
      return;
    }

    void this.notifyExitReady();
  }

  async loadDevices(): Promise<void> {
    this.state.set('loading');

    try {
      const devices = await this.getDevices.execute();
      this.devices.set(devices);
      this.state.set(devices.length === 0 ? 'empty' : 'ready');
    } catch {
      this.devices.set([]);
      this.state.set('error');
    }
  }

  private async notifyExitReady(): Promise<void> {
    await nextFrame();
    await nextFrame();

    const deviceId = this.transition.snapshot()?.deviceId;
    if (deviceId) {
      await waitForDeviceCardThumbBounds(deviceId);
    }

    if (this.transition.kind() === 'exit') {
      this.transition.notifyReady();
    }
  }
}

function nextFrame(): Promise<void> {
  return new Promise((resolve) => {
    requestAnimationFrame(() => resolve());
  });
}
