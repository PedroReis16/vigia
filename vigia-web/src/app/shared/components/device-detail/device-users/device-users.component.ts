import { Component, inject, input, output, signal } from '@angular/core';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { ButtonModule } from '@openng/optimus-ui/button';
import { ConfirmationService } from '@openng/optimus-ui/api';
import { ConfirmDialog } from '@openng/optimus-ui/confirmdialog';
import { MAX_GROUP_USERS } from '@core/constants/device.constants';
import { DeviceUser } from '@core/entities';
import { AuthSessionService, MessageService } from '@core/services';
import {
  GenerateDeviceShareLinkService,
  GetDeviceUsersService,
  RemoveDeviceUserService,
} from '@core/usecases';
import { DeviceUserItemComponent } from '../device-user-item/device-user-item.component';

@Component({
  selector: 'app-device-users',
  standalone: true,
  imports: [TranslateModule, ButtonModule, ConfirmDialog, DeviceUserItemComponent],
  providers: [ConfirmationService],
  templateUrl: './device-users.component.html',
  styleUrl: './device-users.component.css',
})
export class DeviceUsersComponent {
  private readonly getDeviceUsers = inject(GetDeviceUsersService);
  private readonly generateShareLink = inject(GenerateDeviceShareLinkService);
  private readonly removeDeviceUser = inject(RemoveDeviceUserService);
  private readonly authSession = inject(AuthSessionService);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly translate = inject(TranslateService);

  readonly deviceId = input.required<string>();
  readonly isOwner = input.required<boolean>();
  readonly users = input.required<DeviceUser[]>();

  readonly back = output<void>();
  readonly usersChanged = output<void>();
  readonly leftGroup = output<void>();

  readonly sharing = signal(false);
  readonly loading = signal(false);
  readonly maxGroupUsers = MAX_GROUP_USERS;

  get currentUserId(): string | null {
    return this.authSession.getUserId();
  }

  get canShare(): boolean {
    return this.isOwner() && this.users().length < MAX_GROUP_USERS;
  }

  onBack(): void {
    this.back.emit();
  }

  async onShare(): Promise<void> {
    if (this.sharing() || !this.canShare) {
      return;
    }

    this.sharing.set(true);
    try {
      const invite = await this.generateShareLink.execute(this.deviceId());
      await navigator.clipboard.writeText(invite.inviteUrl);

      if (navigator.share) {
        try {
          await navigator.share({
            title: this.translate.instant('DEVICES.USERS.SHARE_SUBJECT'),
            url: invite.inviteUrl,
          });
        } catch {
          // Non-fatal if share sheet is dismissed.
        }
      }

      this.messageService.addMessage({
        message: this.translate.instant('DEVICES.USERS.SHARE_COPIED'),
        type: 'success',
      });
    } catch {
      this.messageService.addMessage({
        message: this.translate.instant('DEVICES.USERS.SHARE_ERROR'),
        type: 'error',
      });
    } finally {
      this.sharing.set(false);
    }
  }

  onRemoveUser(user: DeviceUser): void {
    const isSelf = user.id === this.currentUserId;
    this.confirmationService.confirm({
      header: this.translate.instant(
        isSelf ? 'DEVICES.USERS.LEAVE_TITLE' : 'DEVICES.USERS.REMOVE_TITLE',
      ),
      message: this.translate.instant(
        isSelf ? 'DEVICES.USERS.LEAVE_MESSAGE' : 'DEVICES.USERS.REMOVE_MESSAGE',
        { name: user.name },
      ),
      acceptLabel: this.translate.instant(
        isSelf ? 'DEVICES.USERS.LEAVE_CONFIRM' : 'DEVICES.USERS.REMOVE_CONFIRM',
      ),
      rejectLabel: this.translate.instant('COMMON.CANCEL'),
      accept: () => void this.confirmRemove(user, isSelf),
    });
  }

  private async confirmRemove(user: DeviceUser, isSelf: boolean): Promise<void> {
    try {
      await this.removeDeviceUser.execute(this.deviceId(), user.id);
      if (isSelf) {
        this.messageService.addMessage({
          message: this.translate.instant('DEVICES.USERS.LEAVE_SUCCESS'),
          type: 'success',
        });
        this.leftGroup.emit();
        return;
      }

      this.messageService.addMessage({
        message: this.translate.instant('DEVICES.USERS.REMOVE_SUCCESS'),
        type: 'success',
      });
      this.usersChanged.emit();
    } catch {
      this.messageService.addMessage({
        message: this.translate.instant('DEVICES.USERS.REMOVE_ERROR'),
        type: 'error',
      });
    }
  }
}
