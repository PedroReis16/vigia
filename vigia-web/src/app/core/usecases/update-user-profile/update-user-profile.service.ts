import { HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { UserProfile } from '@core/entities';
import { UserProfileMapper } from '@core/mappers';
import { UserProfileHttpService, UserProfileStoreService } from '@core/services';
import { firstValueFrom } from 'rxjs';
import { ProfileUseCaseError } from '../profile-use-case.error';

export interface UpdateUserProfileInput {
  firstName: string;
  lastName: string;
  phone: string;
}

@Injectable({
  providedIn: 'root',
})
export class UpdateUserProfileService {
  private readonly profileHttp = inject(UserProfileHttpService);
  private readonly store = inject(UserProfileStoreService);

  async execute(input: UpdateUserProfileInput): Promise<UserProfile> {
    try {
      const dto = await firstValueFrom(this.profileHttp.updateProfile(input));
      const profile = UserProfileMapper.fromDto(dto);
      this.store.set(profile);
      return profile;
    } catch (error: unknown) {
      throw this.toError(error);
    }
  }

  private toError(error: unknown): ProfileUseCaseError {
    const code = readErrorCode(error);
    if (code === 'INVALID_PROFILE_NAME') {
      return new ProfileUseCaseError('PROFILE.NAME_INVALID');
    }
    if (code === 'INVALID_PROFILE_PHONE') {
      return new ProfileUseCaseError('PROFILE.PHONE_INVALID');
    }
    return new ProfileUseCaseError('PROFILE.SAVE_ERROR');
  }
}

function readErrorCode(error: unknown): string | null {
  if (!(error instanceof HttpErrorResponse)) {
    return null;
  }

  const code = error.error?.errorCode;
  return typeof code === 'string' ? code : null;
}
