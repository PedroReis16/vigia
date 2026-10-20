import { NgTemplateOutlet } from '@angular/common';
import { Component, computed, effect, inject, OnDestroy, OnInit, signal } from '@angular/core';
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

type PictureDraft =
  | { kind: 'none' }
  | { kind: 'file'; file: File; previewUrl: string }
  | { kind: 'removed' };

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
export class ProfileComponent implements OnInit, OnDestroy {
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
  private readonly pictureDraft = signal<PictureDraft>({ kind: 'none' });
  readonly picturePending = computed(() => this.pictureDraft().kind !== 'none');
  readonly displayedPictureUrl = computed(() => {
    if (this.editing()) {
      const draft = this.pictureDraft();
      if (draft.kind === 'file') {
        return draft.previewUrl;
      }
      if (draft.kind === 'removed') {
        return null;
      }
    }

    return this.profile()?.pictureUrl ?? null;
  });
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

  ngOnDestroy(): void {
    this.revokePicturePreview();
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
    this.setPictureDraft({ kind: 'none' });
    this.editing.set(true);
  }

  onCancelEdit(): void {
    if (this.saving()) {
      return;
    }

    this.setPictureDraft({ kind: 'none' });
    this.editing.set(false);
    this.form.markAsPristine();
  }

  async onSave(): Promise<void> {
    if (this.saving()) {
      return;
    }

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const draft = this.pictureDraft();
    const profileDirty = this.form.dirty;
    if (!profileDirty && draft.kind === 'none') {
      return;
    }

    const { firstName, lastName, phone } = this.form.getRawValue();
    this.saving.set(true);
    try {
      if (profileDirty) {
        const saved = await this.updateProfile.execute({ firstName, lastName, phone });
        this.form.reset({
          firstName: saved.firstName,
          lastName: saved.lastName,
          phone: saved.phone,
        });
      }

      if (draft.kind === 'file') {
        await this.uploadPicture.execute(draft.file);
      } else if (draft.kind === 'removed') {
        await this.removePicture.execute();
      }

      this.setPictureDraft({ kind: 'none' });
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

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (!file || this.saving() || !this.editing()) {
      return;
    }

    if (!isAllowedPicture(file)) {
      this.messageService.addMessage({
        message: this.translate.instant('PROFILE.PICTURE_INVALID'),
        type: 'error',
      });
      return;
    }

    const previewUrl = URL.createObjectURL(file);
    this.setPictureDraft({ kind: 'file', file, previewUrl });
  }

  onRemovePicture(): void {
    if (this.saving() || !this.editing() || !this.displayedPictureUrl()) {
      return;
    }

    if (this.profile()?.pictureUrl) {
      this.setPictureDraft({ kind: 'removed' });
      return;
    }

    this.setPictureDraft({ kind: 'none' });
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

  private setPictureDraft(next: PictureDraft): void {
    this.revokePicturePreview();
    this.pictureDraft.set(next);
  }

  private revokePicturePreview(): void {
    const draft = this.pictureDraft();
    if (draft.kind === 'file') {
      URL.revokeObjectURL(draft.previewUrl);
    }
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
