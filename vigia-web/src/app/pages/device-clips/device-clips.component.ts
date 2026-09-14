import { Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { ButtonModule } from '@openng/optimus-ui/button';
import { GetDeviceService } from '@core/usecases';
import { Device } from '@core/entities';

@Component({
  selector: 'app-device-clips',
  standalone: true,
  imports: [TranslateModule, ButtonModule, RouterLink],
  templateUrl: './device-clips.component.html',
  styleUrl: './device-clips.component.css',
})
export class DeviceClipsComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly getDevice = inject(GetDeviceService);

  readonly device = signal<Device | null>(null);
  deviceId = '';

  ngOnInit(): void {
    this.deviceId = this.route.snapshot.paramMap.get('deviceId') ?? '';
    void this.loadDevice();
  }

  private async loadDevice(): Promise<void> {
    try {
      this.device.set(await this.getDevice.execute(this.deviceId));
    } catch {
      this.device.set(null);
    }
  }
}
