import { Device } from '../entities/classes/device';
import { DeviceDto } from '../entities/DTOs/device.dto';
import { parseDeviceRoom } from '@core/enums';
import { resolveApiAssetUrl } from '@core/helpers';

export class DeviceMapper {
  static fromDto(dto: DeviceDto): Device {
    return new Device(
      String(dto.id),
      dto.name ?? '',
      dto.nickname ?? null,
      dto.ownerId != null ? String(dto.ownerId) : null,
      dto.macAddress ?? '',
      parseDeviceRoom(dto.room ?? null),
      resolveApiAssetUrl(dto.thumbnailUrl),
      dto.isRunning ?? false,
      dto.isClipsEnabled ?? false,
    );
  }

  static fromDtoList(dtos: DeviceDto[]): Device[] {
    return dtos.map((dto) => DeviceMapper.fromDto(dto));
  }
}
