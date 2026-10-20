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
export class GetUserProfileService {
  private readonly profileHttp = inject(UserProfileHttpService);
  private readonly store = inject(UserProfileStoreService);

  async execute(): Promise<UserProfile> {
    try {
      const dto = await firstValueFrom(this.profileHttp.getProfile());
      const profile = UserProfileMapper.fromDto(dto);
      this.store.set(profile);
      return profile;
    } catch (error: unknown) {
      throw this.toError(error);
    }
  }

  private toError(error: unknown): ProfileUseCaseError {
    if (error instanceof HttpErrorResponse) {
      return new ProfileUseCaseError('PROFILE.LOAD_ERROR');
    }
    return new ProfileUseCaseError('PROFILE.LOAD_ERROR');
  }
}
