import { Component, DestroyRef, inject, input, OnInit, output, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { ButtonModule } from '@openng/optimus-ui/button';
import { CardModule } from '@openng/optimus-ui/card';
import { ConfirmationService } from '@openng/optimus-ui/api';
import { ConfirmDialog } from '@openng/optimus-ui/confirmdialog';
import { MAX_GROUP_USERS } from '@core/constants/device.constants';
import { DeviceShareInvite, DeviceUser, eventIncludesDevice } from '@core/entities';
import { AuthSessionService, DeviceGroupsRealtimeService, MessageService } from '@core/services';
import {
  GenerateDeviceShareLinkService,
  GetDeviceUsersService,
  RemoveDeviceUserService,
} from '@core/usecases';
import { DeviceUserItemComponent } from '../device-user-item/device-user-item.component';

@Component({
  selector: 'app-device-users',
  standalone: true,
  imports: [TranslateModule, ButtonModule, CardModule, ConfirmDialog, DeviceUserItemComponent],
  providers: [ConfirmationService],
  templateUrl: './device-users.component.html',
  styleUrl: './device-users.component.css',
})
export class DeviceUsersComponent implements OnInit {
  private readonly getDeviceUsers = inject(GetDeviceUsersService);
  private readonly generateShareLink = inject(GenerateDeviceShareLinkService);
  private readonly removeDeviceUser = inject(RemoveDeviceUserService);
  private readonly authSession = inject(AuthSessionService);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly translate = inject(TranslateService);
  private readonly realtime = inject(DeviceGroupsRealtimeService);
  private readonly destroyRef = inject(DestroyRef);

  readonly deviceId = input.required<string>();
  readonly isOwner = input.required<boolean>();

  readonly back = output<void>();
  readonly usersChanged = output<void>();
  readonly leftGroup = output<void>();

  readonly users = signal<DeviceUser[]>([]);
  readonly loading = signal(true);
  readonly error = signal(false);
  readonly sharing = signal(false);
  readonly sharedInvite = signal<DeviceShareInvite | null>(null);
  readonly linkCopied = signal(false);
  readonly maxGroupUsers = MAX_GROUP_USERS;
  private copyReset: ReturnType<typeof setTimeout> | null = null;

  ngOnInit(): void {
    void this.loadUsers(this.deviceId());
    this.realtime.membershipChanged$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((event) => {
        if (!eventIncludesDevice(event, this.deviceId())) {
          return;
        }

        void this.loadUsers(this.deviceId());
      });
    this.destroyRef.onDestroy(() => {
      if (this.copyReset) {
        clearTimeout(this.copyReset);
      }
    });
  }

  get currentUserId(): string | null {
    return this.authSession.getUserId();
  }

  get canShare(): boolean {
    return this.isOwner() && this.users().length < MAX_GROUP_USERS;
  }

  selectInviteLink(event: FocusEvent): void {
    const input = event.target;
    if (input instanceof HTMLInputElement) {
      input.select();
    }
  }

  formatExpiry(invite: DeviceShareInvite): string {
    return new Intl.DateTimeFormat(undefined, {
      hour: '2-digit',
      minute: '2-digit',
    }).format(invite.expiresAt);
  }

  onBack(): void {
    this.back.emit();
  }

  onRetry(): Promise<void> {
    return this.loadUsers(this.deviceId());
  }

  async loadUsers(deviceId: string): Promise<void> {
    this.loading.set(true);
    this.error.set(false);

    try {
      this.users.set(await this.getDeviceUsers.execute(deviceId));
    } catch {
      this.error.set(true);
    } finally {
      this.loading.set(false);
    }
  }

  async copyInviteLink(): Promise<void> {
    const invite = this.sharedInvite();
    if (!invite) {
      return;
    }

    try {
      await navigator.clipboard.writeText(invite.inviteUrl);
      this.linkCopied.set(true);
      if (this.copyReset) {
        clearTimeout(this.copyReset);
      }
      this.copyReset = setTimeout(() => this.linkCopied.set(false), 2000);
    } catch {
      this.messageService.addMessage({
        message: this.translate.instant('DEVICES.USERS.SHARE_COPY_ERROR'),
        type: 'error',
      });
    }
  }

  async onShare(): Promise<void> {
    if (this.sharing() || !this.canShare) {
      return;
    }

    this.sharing.set(true);
    try {
      const invite = await this.generateShareLink.execute(this.deviceId());
      this.sharedInvite.set(invite);

      try {
        await navigator.clipboard.writeText(invite.inviteUrl);
      } catch {
        // The link stays on screen when the clipboard is unavailable.
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
      await this.loadUsers(this.deviceId());
      this.usersChanged.emit();
    } catch {
      this.messageService.addMessage({
        message: this.translate.instant('DEVICES.USERS.REMOVE_ERROR'),
        type: 'error',
      });
    }
  }
}
