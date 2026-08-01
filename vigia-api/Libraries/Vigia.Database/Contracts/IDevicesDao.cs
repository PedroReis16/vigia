using Vigia.Models.Entities;
using Vigia.Models.Enums;

namespace Vigia.Database.Contracts;

public interface IDevicesDao : IRepository<Device>
{
    Task<List<Device>> GetUserDevicesAsync(Guid userId, string? nickname, DeviceRooms? room, bool onlyShared, bool onlyOwned, int page, int pageSize);
    Task UpdateDeviceGroupAsync(Device device);
    Task<List<Guid>> GetDeviceIdsByGroupAsync(Guid groupId);
}
