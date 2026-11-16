import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideRouter } from '@angular/router';
import { provideOptimus } from '@openng/optimus-ui/config';
import { ConfirmationService } from '@openng/optimus-ui/api';
import { TranslateModule } from '@ngx-translate/core';
import { vi } from 'vitest';
import { UserProfile } from '@core/entities';
import { MessageService, UserProfileStoreService } from '@core/services';
import {
  DeleteAccountService,
  GetUserProfileService,
  RemoveProfilePictureService,
  UpdateUserProfileService,
  UploadProfilePictureService,
} from '@core/usecases';
import { VigiaTheme } from '@shared/theme/vigia.theme';
import { ProfileComponent } from './profile.component';

describe('ProfileComponent', () => {
  let fixture: ComponentFixture<ProfileComponent>;
  let store: UserProfileStoreService;
  let upload: { execute: ReturnType<typeof vi.fn> };
  let remove: { execute: ReturnType<typeof vi.fn> };
  let update: { execute: ReturnType<typeof vi.fn> };
  let deleteAccount: { execute: ReturnType<typeof vi.fn> };

  const profile = new UserProfile(
    'user-1',
    'Ana Lima',
    'Ana',
    'Lima',
    'ana@vigia.test',
    '11999990000',
    'https://example.test/picture.jpg',
    true,
  );

  beforeEach(async () => {
    upload = { execute: vi.fn().mockResolvedValue(profile) };
    remove = { execute: vi.fn().mockResolvedValue(profile) };
    update = { execute: vi.fn().mockResolvedValue(profile) };
    deleteAccount = { execute: vi.fn().mockResolvedValue(undefined) };

    await TestBed.configureTestingModule({
      imports: [ProfileComponent, TranslateModule.forRoot()],
      providers: [
        MessageService,
        {
          provide: GetUserProfileService,
          useValue: { execute: vi.fn().mockResolvedValue(profile) },
        },
        { provide: UploadProfilePictureService, useValue: upload },
        { provide: RemoveProfilePictureService, useValue: remove },
        { provide: UpdateUserProfileService, useValue: update },
        { provide: DeleteAccountService, useValue: deleteAccount },
        provideRouter([]),
        provideAnimationsAsync(),
        provideOptimus({
          theme: {
            preset: VigiaTheme,
            options: { darkModeSelector: false },
          },
        }),
      ],
    }).compileComponents();

    store = TestBed.inject(UserProfileStoreService);
    store.set(profile);
    fixture = TestBed.createComponent(ProfileComponent);
    fixture.detectChanges();
  });

  it('shows the profile as read-only, with delete and without the edit form', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('[data-testid="profile-name"]')?.textContent).toContain(
      'Ana Lima',
    );
    expect(compiled.querySelector('[data-testid="profile-email"]')?.textContent).toContain(
      'ana@vigia.test',
    );
    expect(compiled.querySelector('[data-testid="profile-phone"]')?.textContent).toContain(
      '11999990000',
    );
    expect(compiled.querySelector('[data-testid="profile-delete"]')).toBeTruthy();
    expect(compiled.querySelector('[data-testid="profile-edit"]')).toBeTruthy();
    expect(compiled.querySelector('[data-testid="profile-first-name"]')?.textContent).toContain(
      'Ana',
    );
    expect(compiled.querySelector('input[data-testid="profile-first-name"]')).toBeNull();
    expect(compiled.querySelector('[data-testid="profile-picture-button"]')).toBeNull();
    expect(compiled.querySelector('[data-testid="profile-remove-picture"]')).toBeNull();
    const account = compiled.querySelector('p-card');
    const plan = compiled.querySelector('[data-testid="profile-plan"]');
    expect(account).toBeTruthy();
    expect(plan).toBeTruthy();
    expect(account!.compareDocumentPosition(plan!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('reveals the form and the picture overlay when editing', () => {
    fixture.componentInstance.onEdit();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('[data-testid="profile-picture-button"]')).toBeTruthy();
    expect(
      (compiled.querySelector('[data-testid="profile-first-name"]') as HTMLInputElement).value,
    ).toBe('Ana');
    expect(
      (compiled.querySelector('[data-testid="profile-phone"]') as HTMLInputElement).value,
    ).toBe('11999990000');
    expect(compiled.querySelector('[data-testid="profile-save"]')).toBeTruthy();
    expect(compiled.querySelector('[data-testid="profile-delete"]')).toBeNull();
    expect(compiled.querySelector('[data-testid="profile-remove-picture"]')).toBeTruthy();
  });

  it('returns to the read-only view when edit is cancelled', () => {
    fixture.componentInstance.onEdit();
    fixture.componentInstance.onCancelEdit();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('[data-testid="profile-edit"]')).toBeTruthy();
    expect(compiled.querySelector('[data-testid="profile-save"]')).toBeNull();
    expect(compiled.querySelector('[data-testid="profile-delete"]')).toBeTruthy();
  });

  it('saves the edited name and phone', async () => {
    fixture.componentInstance.onEdit();
    fixture.componentInstance.form.controls.firstName.setValue('Ana Paula');
    fixture.componentInstance.form.controls.phone.setValue('11988887777');
    fixture.componentInstance.form.markAsDirty();

    await fixture.componentInstance.onSave();

    expect(update.execute).toHaveBeenCalledWith({
      firstName: 'Ana Paula',
      lastName: 'Lima',
      phone: '11988887777',
    });
    expect(fixture.componentInstance.editing()).toBe(false);
  });

  it('does not save an invalid phone', async () => {
    fixture.componentInstance.form.controls.phone.setValue('abc');
    fixture.componentInstance.form.markAsDirty();

    await fixture.componentInstance.onSave();

    expect(update.execute).not.toHaveBeenCalled();
  });

  it('previews an allowed picture and uploads it only when saving', async () => {
    const file = selectPicture(fixture);

    expect(upload.execute).not.toHaveBeenCalled();
    expect(pictureSource(fixture)).toContain('blob:');
    expect(saveButton(fixture).disabled).toBe(false);

    await fixture.componentInstance.onSave();

    expect(upload.execute).toHaveBeenCalledWith(file);
    expect(fixture.componentInstance.editing()).toBe(false);
    expect(remove.execute).not.toHaveBeenCalled();
  });

  it('rejects a file that is too large', () => {
    fixture.componentInstance.onEdit();
    fixture.detectChanges();
    const message = TestBed.inject(MessageService);
    const input = fixture.nativeElement.querySelector(
      '[data-testid="profile-picture-input"]',
    ) as HTMLInputElement;
    const file = new File([new Uint8Array(8)], 'huge.jpg', { type: 'image/jpeg' });
    Object.defineProperty(file, 'size', { value: 3 * 1024 * 1024 });
    const list = {
      0: file,
      length: 1,
      item: () => file,
    } as unknown as FileList;
    Object.defineProperty(input, 'files', { value: list });

    input.dispatchEvent(new Event('change'));
    fixture.detectChanges();

    expect(upload.execute).not.toHaveBeenCalled();
    expect(message.messages()?.type).toBe('error');
    expect(pictureSource(fixture)).toBe('https://example.test/picture.jpg');
    expect(saveButton(fixture).disabled).toBe(true);
  });

  it('stages picture removal until save', async () => {
    fixture.componentInstance.onEdit();
    fixture.detectChanges();
    fixture.componentInstance.onRemovePicture();
    fixture.detectChanges();

    expect(remove.execute).not.toHaveBeenCalled();
    expect(pictureSource(fixture)).toBeNull();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="profile-remove-picture"]'),
    ).toBeNull();
    expect(saveButton(fixture).disabled).toBe(false);

    await fixture.componentInstance.onSave();

    expect(remove.execute).toHaveBeenCalled();
    expect(update.execute).not.toHaveBeenCalled();
    expect(fixture.componentInstance.editing()).toBe(false);
  });

  it('discards a staged picture when edit is cancelled', () => {
    selectPicture(fixture);
    fixture.componentInstance.onCancelEdit();
    fixture.detectChanges();

    expect(upload.execute).not.toHaveBeenCalled();
    expect(remove.execute).not.toHaveBeenCalled();
    expect(pictureSource(fixture)).toBe('https://example.test/picture.jpg');
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="profile-edit"]'),
    ).toBeTruthy();
  });

  it('discards a staged removal when edit is cancelled', () => {
    fixture.componentInstance.onEdit();
    fixture.componentInstance.onRemovePicture();
    fixture.componentInstance.onCancelEdit();
    fixture.detectChanges();

    expect(remove.execute).not.toHaveBeenCalled();
    expect(pictureSource(fixture)).toBe('https://example.test/picture.jpg');
  });

  it('saves profile fields and a staged picture together', async () => {
    const file = selectPicture(fixture);
    fixture.componentInstance.form.controls.firstName.setValue('Ana Paula');
    fixture.componentInstance.form.markAsDirty();

    await fixture.componentInstance.onSave();

    expect(update.execute).toHaveBeenCalledWith({
      firstName: 'Ana Paula',
      lastName: 'Lima',
      phone: '11999990000',
    });
    expect(upload.execute).toHaveBeenCalledWith(file);
  });

  it('keeps the staged picture when saving it fails', async () => {
    upload.execute.mockRejectedValueOnce(new Error('upload failed'));
    selectPicture(fixture);

    await fixture.componentInstance.onSave();

    expect(fixture.componentInstance.editing()).toBe(true);
    expect(pictureSource(fixture)).toContain('blob:');
    expect(saveButton(fixture).disabled).toBe(false);
  });

  it('hides account deletion for the super admin', () => {
    store.set(
      new UserProfile(
        'admin',
        'Super Admin',
        'Super',
        'Admin',
        'admin@vigia.local',
        '11999999999',
        null,
        false,
      ),
    );
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('[data-testid="profile-name"]')?.textContent).toContain(
      'Super Admin',
    );
    expect(compiled.querySelector('[data-testid="profile-delete"]')).toBeNull();
    expect(compiled.querySelector('[data-testid="profile-edit"]')).toBeTruthy();
  });

  it('deletes the account after confirmation', () => {
    const confirmation = fixture.debugElement.injector.get(ConfirmationService);
    vi.spyOn(confirmation, 'confirm').mockImplementation((config) => {
      config.accept?.();
      return confirmation;
    });

    fixture.componentInstance.onDeleteAccount();

    expect(deleteAccount.execute).toHaveBeenCalled();
  });
});

function selectPicture(fixture: ComponentFixture<ProfileComponent>): File {
  fixture.componentInstance.onEdit();
  fixture.detectChanges();
  const input = fixture.nativeElement.querySelector(
    '[data-testid="profile-picture-input"]',
  ) as HTMLInputElement;
  const file = new File([new Uint8Array([1, 2, 3])], 'avatar.png', { type: 'image/png' });
  const list = {
    0: file,
    length: 1,
    item: () => file,
  } as unknown as FileList;
  Object.defineProperty(input, 'files', { value: list });
  input.dispatchEvent(new Event('change'));
  fixture.detectChanges();
  return file;
}

function pictureSource(fixture: ComponentFixture<ProfileComponent>): string | null {
  const image = (fixture.nativeElement as HTMLElement).querySelector(
    '.profile__avatar img',
  ) as HTMLImageElement | null;
  return image?.getAttribute('src') ?? null;
}

function saveButton(fixture: ComponentFixture<ProfileComponent>): HTMLButtonElement {
  const button = (fixture.nativeElement as HTMLElement).querySelector(
    '[data-testid="profile-save"] button',
  );
  if (!(button instanceof HTMLButtonElement)) {
    throw new Error('Save button was not rendered');
  }
  return button;
}
