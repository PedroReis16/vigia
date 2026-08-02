using Vigia.API.Controllers;
using Vigia.API.Models.DTOs.Devices;
using Vigia.Models.Enums;

namespace Vigia.API.Contracts;

public interface IDevicesService
{
    Task<DeviceDTO?> GetDeviceAsync(Guid deviceId);
    byte[]? GetDeviceFrame(Guid deviceId);
    Task<List<DeviceDTO>> ListDevicesAsync(Guid userId, string? nickname, DeviceRooms? room, bool onlyShared, bool onlyOwned, int page, int pageSize);
    Task RegisterDeviceAsync(NewDeviceDTO newDevice);
    DeviceProvisionConfigDTO GetProvisionConfig();
    void SaveDeviceFrame(Guid deviceId, Stream stream);
    Task TrackDeviceUserAsync(Guid deviceId, Guid userId);
    Task UntrackedDeviceUserAsync(Guid deviceId, Guid userId);
    Task UpdateDeviceAsync(Guid userId, Guid deviceId, UpdateDeviceDTO updatedDevice);
}