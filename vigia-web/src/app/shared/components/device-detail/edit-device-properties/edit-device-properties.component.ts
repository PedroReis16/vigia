import { Component, inject, input, OnInit, output, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { ButtonModule } from '@openng/optimus-ui/button';
import { CardModule } from '@openng/optimus-ui/card';
import { InputTextModule } from '@openng/optimus-ui/inputtext';
import { Select } from '@openng/optimus-ui/select';
import { ToggleSwitch } from '@openng/optimus-ui/toggleswitch';
import { ConfirmationService } from '@openng/optimus-ui/api';
import { ConfirmDialog } from '@openng/optimus-ui/confirmdialog';
import { Device } from '@core/entities';
import { DeviceRooms, deviceRoomI18nKey } from '@core/enums';
import { MessageService } from '@core/services';
import { UpdateDeviceService } from '@core/usecases';

@Component({
  selector: 'app-edit-device-properties',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    TranslateModule,
    ButtonModule,
    CardModule,
    InputTextModule,
    Select,
    ToggleSwitch,
    ConfirmDialog,
  ],
  providers: [ConfirmationService],
  templateUrl: './edit-device-properties.component.html',
  styleUrl: './edit-device-properties.component.css',
})
export class EditDevicePropertiesComponent implements OnInit {
  private readonly updateDevice = inject(UpdateDeviceService);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly translate = inject(TranslateService);

  readonly device = input.required<Device>();

  readonly back = output<void>();
  readonly saved = output<Device>();

  readonly saving = signal(false);
  clipsInfoVisible = false;

  readonly roomOptions = Object.values(DeviceRooms).map((room) => ({
    label: room,
    value: room,
  }));

  form = new FormGroup({
    nickname: new FormControl('', { nonNullable: true }),
    room: new FormControl<DeviceRooms | null>(null),
    isClipsEnabled: new FormControl(false, { nonNullable: true }),
  });

  ngOnInit(): void {
    const device = this.device();
    this.form.patchValue({
      nickname: device.nickname ?? '',
      room: device.room,
      isClipsEnabled: device.isClipsEnabled,
    });
  }

  get hasUnsavedChanges(): boolean {
    const device = this.device();
    const value = this.form.getRawValue();
    const nickname = value.nickname.trim();
    const originalNickname = (device.nickname ?? '').trim();
    return (
      nickname !== originalNickname ||
      value.room !== device.room ||
      value.isClipsEnabled !== device.isClipsEnabled
    );
  }

  onBack(): void {
    if (this.saving()) {
      return;
    }

    if (this.hasUnsavedChanges) {
      this.confirmationService.confirm({
        header: this.translate.instant('DEVICES.EDIT.DISCARD_TITLE'),
        message: this.translate.instant('DEVICES.EDIT.DISCARD_MESSAGE'),
        acceptLabel: this.translate.instant('DEVICES.EDIT.DISCARD'),
        rejectLabel: this.translate.instant('COMMON.CANCEL'),
        accept: () => this.back.emit(),
      });
      return;
    }

    this.back.emit();
  }

  deviceRoomKey(room: DeviceRooms): string {
    return deviceRoomI18nKey(room);
  }

  async onSave(): Promise<void> {
    if (this.saving() || !this.hasUnsavedChanges) {
      return;
    }

    this.saving.set(true);
    const value = this.form.getRawValue();
    const nickname = value.nickname.trim();

    try {
      const updated = await this.updateDevice.execute(this.device().id, {
        nickname: nickname || null,
        room: value.room,
        isClipsEnabled: value.isClipsEnabled,
      });
      this.messageService.addMessage({
        message: this.translate.instant('DEVICES.EDIT.SUCCESS'),
        type: 'success',
      });
      this.saved.emit(updated);
    } catch {
      this.messageService.addMessage({
        message: this.translate.instant('DEVICES.EDIT.ERROR'),
        type: 'error',
      });
    } finally {
      this.saving.set(false);
    }
  }
}
