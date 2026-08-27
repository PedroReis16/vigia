import { Component, inject, input, output, signal } from '@angular/core';
import { TranslateModule } from '@ngx-translate/core';
import { CardModule } from '@openng/optimus-ui/card';
import { Skeleton } from '@openng/optimus-ui/skeleton';
import { MAX_GROUP_USERS } from '@core/constants/device.constants';
import { Device, DeviceUser } from '@core/entities';
import { deviceRoomI18nKey } from '@core/enums';
import { isDeviceOwner } from '@core/helpers';
import { AuthSessionService } from '@core/services';
import { DeviceDetailActionRowComponent } from '../device-detail-action-row/device-detail-action-row.component';
import { DeviceUserItemComponent } from '../device-user-item/device-user-item.component';
import { EditDevicePropertiesComponent } from '../edit-device-properties/edit-device-properties.component';
import { DeviceUsersComponent } from '../device-users/device-users.component';

export type DeviceDetailsPane = 'details' | 'edit' | 'users';

@Component({
  selector: 'app-device-details-panel',
  standalone: true,
  imports: [
    TranslateModule,
    CardModule,
    Skeleton,
    DeviceDetailActionRowComponent,
    DeviceUserItemComponent,
    EditDevicePropertiesComponent,
    DeviceUsersComponent,
  ],
  templateUrl: './device-details-panel.component.html',
  styleUrl: './device-details-panel.component.css',
})
export class DeviceDetailsPanelComponent {
  private readonly authSession = inject(AuthSessionService);

  readonly device = input.required<Device>();
  readonly users = input<DeviceUser[]>([]);
  readonly usersLoading = input(false);
  readonly usersError = input(false);

  readonly deviceUpdated = output<Device>();
  readonly usersChanged = output<void>();
  readonly leftGroup = output<void>();

  readonly pane = signal<DeviceDetailsPane>('details');
  readonly maxGroupUsers = MAX_GROUP_USERS;

  previewUsers(users: DeviceUser[]): DeviceUser[] {
    return users.slice(0, 3);
  }

  isOwner(device: Device): boolean {
    return isDeviceOwner(device, this.authSession.getUserId());
  }

  openEdit(): void {
    this.pane.set('edit');
  }

  openUsers(): void {
    this.pane.set('users');
  }

  backToDetails(): void {
    this.pane.set('details');
  }

  onDeviceSaved(device: Device): void {
    this.deviceUpdated.emit(device);
    this.backToDetails();
  }

  roomKey(device: Device): string {
    return deviceRoomI18nKey(device.room);
  }
}
