using Vigia.API.Models.DTOs.Devices;

namespace Vigia.API.Contracts;

public interface IDeviceUsersService
{
    Task<List<DeviceUserDTO>> GetDeviceUsersAsync(Guid deviceId, Guid requestingUserId);
    Task RemoveDeviceUserAsync(Guid deviceId, Guid targetUserId, Guid requestingUserId);
}
