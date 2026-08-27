import { Component, computed, ElementRef, inject, input, signal, viewChild } from '@angular/core';
import { Router } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { CardModule } from '@openng/optimus-ui/card';
import { Device } from '@core/entities/classes/device';
import { deviceRoomI18nKey } from '@core/enums';
import { captureDeviceCardSnapshot } from '@core/helpers/device-card-bounds.helper';
import { DeviceDetailTransitionService } from '@core/services';

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

  private readonly router = inject(Router);
  private readonly transition = inject(DeviceDetailTransitionService);

  readonly cardFrame = viewChild<ElementRef<HTMLElement>>('cardFrame');
  readonly imageFailed = signal(false);

  readonly hideThumbDuringExit = computed(() => {
    const device = this.device();
    const snapshot = this.transition.snapshot();
    return (
      !this.skeleton() &&
      !!device &&
      this.transition.kind() === 'exit' &&
      !this.transition.settled() &&
      snapshot?.deviceId === device.id
    );
  });

  roomKey(device: Device): string {
    return deviceRoomI18nKey(device.room);
  }

  onImageError(): void {
    this.imageFailed.set(true);
  }

  async onOpen(event: Event): Promise<void> {
    const device = this.device();
    if (!device || this.skeleton()) {
      return;
    }

    event.preventDefault();

    const frame = this.cardFrame()?.nativeElement;
    const snapshot = frame
      ? captureDeviceCardSnapshot(frame, {
          deviceId: device.id,
          displayName: device.displayName,
          thumbnailUrl: device.thumbnailUrl,
          imageFailed: this.imageFailed(),
        })
      : null;

    if (snapshot && !this.prefersReducedMotion()) {
      this.transition.armEnter(snapshot);
    }

    await this.router.navigate(['/devices', device.id]);
  }

  private prefersReducedMotion(): boolean {
    return (
      typeof window !== 'undefined' &&
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    );
  }
}
