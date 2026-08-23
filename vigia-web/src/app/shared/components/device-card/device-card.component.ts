import { Component, input, signal } from '@angular/core';
import { TranslateModule } from '@ngx-translate/core';
import { CardModule } from '@openng/optimus-ui/card';
import { Device } from '@core/entities/classes/device';
import { deviceRoomI18nKey } from '@core/enums';

@Component({
  selector: 'app-device-card',
  standalone: true,
  imports: [CardModule, TranslateModule],
  templateUrl: './device-card.component.html',
  styleUrl: './device-card.component.css',
})
export class DeviceCardComponent {
  /** Required when `skeleton` is false. */
  readonly device = input<Device | null>(null);
  readonly skeleton = input(false);

  readonly imageFailed = signal(false);

  roomKey(device: Device): string {
    return deviceRoomI18nKey(device.room);
  }

  onImageError(): void {
    this.imageFailed.set(true);
  }
}
