import { UserProfileDto } from '@core/entities/DTOs/user-profile.dto';
import { UserProfile } from '@core/entities/classes/user-profile';
import { resolveApiAssetUrl } from '@core/helpers';

export class UserProfileMapper {
  static fromDto(dto: UserProfileDto): UserProfile {
    return new UserProfile(
      String(dto.id),
      dto.name ?? '',
      dto.firstName ?? '',
      dto.lastName ?? '',
      dto.email ?? '',
      dto.phone ?? '',
      resolveApiAssetUrl(dto.pictureUrl),
      dto.canDeleteAccount !== false,
    );
  }
}
