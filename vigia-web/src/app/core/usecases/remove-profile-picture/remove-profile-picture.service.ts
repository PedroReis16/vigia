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
export class RemoveProfilePictureService {
  private readonly profileHttp = inject(UserProfileHttpService);
  private readonly store = inject(UserProfileStoreService);

  async execute(): Promise<UserProfile> {
    try {
      const dto = await firstValueFrom(this.profileHttp.removePicture());
      const profile = UserProfileMapper.fromDto(dto);
      this.store.set(profile);
      return profile;
    } catch (error: unknown) {
      if (error instanceof HttpErrorResponse) {
        throw new ProfileUseCaseError('PROFILE.PICTURE_ERROR');
      }
      throw new ProfileUseCaseError('PROFILE.PICTURE_ERROR');
    }
  }
}
