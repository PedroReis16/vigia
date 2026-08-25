import { Component, input, output } from '@angular/core';
import { TranslateModule } from '@ngx-translate/core';
import { DeviceUser } from '@core/entities';

@Component({
  selector: 'app-device-user-item',
  standalone: true,
  imports: [TranslateModule],
  templateUrl: './device-user-item.component.html',
  styleUrl: './device-user-item.component.css',
})
export class DeviceUserItemComponent {
  readonly user = input.required<DeviceUser>();
  readonly showAction = input(false);
  readonly actionIcon = input<'remove' | 'leave' | 'arrow' | null>(null);

  readonly action = output<void>();

  onAction(event: Event): void {
    event.stopPropagation();
    this.action.emit();
  }
}
