using Vigia.Models.Entities;
using Vigia.Models.Enums;

namespace Vigia.Database.Contracts;

public interface IDevicesDao : IRepository<Device>
{
    Task<List<Device>> GetUserDevicesAsync(Guid userId, string? nickname = null, DeviceRooms? room = null, bool onlyShared = false, bool onlyOwned = false, int page = 1, int pageSize = 10);
    Task UpdateDeviceGroupAsync(Device device);
    Task<List<Guid>> GetDeviceIdsByGroupAsync(Guid groupId);
}
