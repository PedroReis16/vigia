import { Component, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { TranslateModule } from '@ngx-translate/core';
import { ButtonModule } from '@openng/optimus-ui/button';
import { Device } from '@core/entities/classes/device';
import { DeviceGroupsRealtimeService } from '@core/services';
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
export class DevicesComponent implements OnInit {
  private readonly getDevices = inject(GetDevicesService);
  private readonly realtime = inject(DeviceGroupsRealtimeService);
  private readonly destroyRef = inject(DestroyRef);

  readonly state = signal<DevicesViewState>('loading');
  readonly devices = signal<Device[]>([]);
  readonly skeletonSlots = [0, 1, 2];

  ngOnInit(): void {
    void this.loadDevices();
    this.realtime.membershipChanged$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        void this.loadDevices();
      });
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
}
