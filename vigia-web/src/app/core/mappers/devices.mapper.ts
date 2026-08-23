import { Device } from '../entities/classes/device';
import { DeviceDto } from '../entities/DTOs/device.dto';

export class DeviceMapper {
  static fromDto(dto: DeviceDto): Device {
    return new Device();
  }
}
