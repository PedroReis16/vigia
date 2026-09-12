import { DeviceUserDto } from '@core/entities/DTOs/device-user.dto';
import { DeviceUser } from '@core/entities/classes/device-user';
import { resolveApiAssetUrl } from '@core/helpers';

export class DeviceUserMapper {
  static fromDto(dto: DeviceUserDto): DeviceUser {
    return new DeviceUser(
      String(dto.id),
      dto.name,
      resolveApiAssetUrl(dto.userPictureUrl),
      dto.isOwner,
    );
  }

  static fromDtoList(dtos: DeviceUserDto[]): DeviceUser[] {
    return dtos.map((dto) => DeviceUserMapper.fromDto(dto));
  }
}
