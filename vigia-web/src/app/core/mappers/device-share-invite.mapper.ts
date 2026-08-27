import { DeviceShareInviteDto } from '@core/entities/DTOs/device-share-invite.dto';
import { DeviceShareInvite } from '@core/entities/classes/device-share-invite';

export class DeviceShareInviteMapper {
  static fromDto(dto: DeviceShareInviteDto): DeviceShareInvite {
    return new DeviceShareInvite(dto.token, dto.inviteUrl, new Date(dto.expiresAt));
  }
}
