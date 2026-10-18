import { HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { UserProfile } from '@core/entities';
import { UserProfileMapper } from '@core/mappers';
import { UserProfileHttpService, UserProfileStoreService } from '@core/services';
import { firstValueFrom } from 'rxjs';
import { ProfileUseCaseError } from '../profile-use-case.error';

@Injectable({
  providedIn: 'root',
})
export class UploadProfilePictureService {
  private readonly profileHttp = inject(UserProfileHttpService);
  private readonly store = inject(UserProfileStoreService);

  async execute(file: File): Promise<UserProfile> {
    try {
      const dto = await firstValueFrom(this.profileHttp.uploadPicture(file));
      const profile = UserProfileMapper.fromDto(dto);
      this.store.set(profile);
      return profile;
    } catch (error: unknown) {
      throw this.toError(error);
    }
  }

  private toError(error: unknown): ProfileUseCaseError {
    const code = readErrorCode(error);
    if (code === 'INVALID_PROFILE_PICTURE' || code === 'PROFILE_PICTURE_TOO_LARGE') {
      return new ProfileUseCaseError('PROFILE.PICTURE_INVALID');
    }
    return new ProfileUseCaseError('PROFILE.PICTURE_ERROR');
  }
}

function readErrorCode(error: unknown): string | null {
  if (!(error instanceof HttpErrorResponse)) {
    return null;
  }

  const code = error.error?.errorCode;
  return typeof code === 'string' ? code : null;
}
