import { NgTemplateOutlet } from '@angular/common';
import { Component, computed, effect, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { ConfirmationService } from '@openng/optimus-ui/api';
import { Avatar } from '@openng/optimus-ui/avatar';
import { ButtonModule } from '@openng/optimus-ui/button';
import { CardModule } from '@openng/optimus-ui/card';
import { ConfirmDialog } from '@openng/optimus-ui/confirmdialog';
import { InputTextModule } from '@openng/optimus-ui/inputtext';
import { profileInitials } from '@core/helpers';
import { MessageService, UserProfileStoreService } from '@core/services';
import {
  DeleteAccountService,
  GetUserProfileService,
  ProfileUseCaseError,
  RemoveProfilePictureService,
  UpdateUserProfileService,
  UploadProfilePictureService,
} from '@core/usecases';
import { ProfilePlanComponent } from './profile-plan/profile-plan.component';

const MAX_PICTURE_BYTES = 2 * 1024 * 1024;
const PHONE_PATTERN = /^[0-9+() .-]{8,16}$/;

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [
    NgTemplateOutlet,
    ReactiveFormsModule,
    TranslateModule,
    Avatar,
    ButtonModule,
    CardModule,
    ConfirmDialog,
    InputTextModule,
    ProfilePlanComponent,
  ],
  providers: [ConfirmationService],
  templateUrl: './profile.component.html',
  styleUrl: './profile.component.css',
})
export class ProfileComponent implements OnInit {
  private readonly store = inject(UserProfileStoreService);
  private readonly getProfile = inject(GetUserProfileService);
  private readonly updateProfile = inject(UpdateUserProfileService);
  private readonly deleteAccount = inject(DeleteAccountService);
  private readonly uploadPicture = inject(UploadProfilePictureService);
  private readonly removePicture = inject(RemoveProfilePictureService);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly translate = inject(TranslateService);
  private readonly router = inject(Router);
  private readonly formBuilder = inject(FormBuilder);

  readonly profile = this.store.profile;
  readonly saving = signal(false);
  readonly editing = signal(false);
  readonly form = this.formBuilder.nonNullable.group({
    firstName: ['', [Validators.required, Validators.maxLength(64)]],
    lastName: ['', [Validators.required, Validators.maxLength(64)]],
    phone: ['', [Validators.required, Validators.pattern(PHONE_PATTERN)]],
  });
  readonly initials = computed(() => {
    const profile = this.profile();
    if (!profile) {
      return '';
    }
    return profileInitials(profile.name, profile.email);
  });

  constructor() {
    effect(() => {
      const current = this.profile();
      if (!current || this.saving() || this.form.dirty) {
        return;
      }

      this.form.reset({
        firstName: current.firstName,
        lastName: current.lastName,
        phone: current.phone,
      });
    });
  }

  ngOnInit(): void {
    void this.getProfile.execute().catch(() => {
      this.messageService.addMessage({
        message: this.translate.instant('PROFILE.LOAD_ERROR'),
        type: 'error',
      });
    });
  }

  onBack(): void {
    void this.router.navigate(['/devices']);
  }

  onEdit(): void {
    const current = this.profile();
    if (!current || this.saving()) {
      return;
    }

    this.form.reset({
      firstName: current.firstName,
      lastName: current.lastName,
      phone: current.phone,
    });
    this.editing.set(true);
  }

  onCancelEdit(): void {
    if (this.saving()) {
      return;
    }

    this.editing.set(false);
    this.form.markAsPristine();
  }

  async onSave(): Promise<void> {
    if (this.form.invalid || this.saving()) {
      this.form.markAllAsTouched();
      return;
    }

    const { firstName, lastName, phone } = this.form.getRawValue();
    this.saving.set(true);
    try {
      const saved = await this.updateProfile.execute({ firstName, lastName, phone });
      this.form.reset({
        firstName: saved.firstName,
        lastName: saved.lastName,
        phone: saved.phone,
      });
      this.editing.set(false);
      this.messageService.addMessage({
        message: this.translate.instant('PROFILE.SAVED'),
        type: 'success',
      });
    } catch (error: unknown) {
      const key = error instanceof ProfileUseCaseError ? error.messageKey : 'PROFILE.SAVE_ERROR';
      this.messageService.addMessage({
        message: this.translate.instant(key),
        type: 'error',
      });
    } finally {
      this.saving.set(false);
    }
  }

  onDeleteAccount(): void {
    if (this.saving()) {
      return;
    }

    this.confirmationService.confirm({
      header: this.translate.instant('PROFILE.DELETE_TITLE'),
      message: this.translate.instant('PROFILE.DELETE_MESSAGE'),
      acceptLabel: this.translate.instant('PROFILE.DELETE_CONFIRM'),
      rejectLabel: this.translate.instant('COMMON.CANCEL'),
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => void this.confirmDelete(),
    });
  }

  async onFileSelected(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (!file || this.saving()) {
      return;
    }

    if (!isAllowedPicture(file)) {
      this.messageService.addMessage({
        message: this.translate.instant('PROFILE.PICTURE_INVALID'),
        type: 'error',
      });
      return;
    }

    this.saving.set(true);
    try {
      await this.uploadPicture.execute(file);
    } catch (error: unknown) {
      this.showPictureError(error);
    } finally {
      this.saving.set(false);
    }
  }

  async onRemovePicture(): Promise<void> {
    if (this.saving() || !this.profile()?.pictureUrl) {
      return;
    }

    this.saving.set(true);
    try {
      await this.removePicture.execute();
    } catch (error: unknown) {
      this.showPictureError(error);
    } finally {
      this.saving.set(false);
    }
  }

  private async confirmDelete(): Promise<void> {
    this.saving.set(true);
    try {
      await this.deleteAccount.execute();
    } catch (error: unknown) {
      const key = error instanceof ProfileUseCaseError ? error.messageKey : 'PROFILE.DELETE_ERROR';
      this.messageService.addMessage({
        message: this.translate.instant(key),
        type: 'error',
      });
      this.saving.set(false);
    }
  }

  private showPictureError(error: unknown): void {
    const key = error instanceof ProfileUseCaseError ? error.messageKey : 'PROFILE.PICTURE_ERROR';
    this.messageService.addMessage({
      message: this.translate.instant(key),
      type: 'error',
    });
  }
}

function isAllowedPicture(file: File): boolean {
  if (file.size <= 0 || file.size > MAX_PICTURE_BYTES) {
    return false;
  }

  const type = file.type.toLowerCase();
  if (type === 'image/jpeg' || type === 'image/png' || type === 'image/webp') {
    return true;
  }

  return /\.(jpe?g|png|webp)$/i.test(file.name);
}
