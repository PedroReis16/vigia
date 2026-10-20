import { DeviceClip } from '@core/entities/classes/device-clip';
import { DeviceClipDto } from '@core/entities/DTOs/device-clip.dto';
import { ClipStatus, parseClipStatus } from '@core/enums';
import { resolveApiAssetUrl } from '@core/helpers';

export class DeviceClipMapper {
  static fromDto(dto: DeviceClipDto): DeviceClip {
    return new DeviceClip(
      String(dto.id),
      String(dto.deviceId),
      parseClipStatus(dto.status) ?? ClipStatus.Failed,
      dto.frameCount ?? 0,
      dto.fps ?? 0,
      new Date(dto.createdAt),
      resolveApiAssetUrl(dto.thumbnailUrl),
      resolveApiAssetUrl(dto.playbackUrl),
    );
  }

  static fromDtoList(dtos: DeviceClipDto[]): DeviceClip[] {
    return dtos.map((dto) => DeviceClipMapper.fromDto(dto));
  }
}
