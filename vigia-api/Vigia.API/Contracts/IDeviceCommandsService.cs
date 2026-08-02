using Vigia.API.Models.DTOs.Devices;
using Vigia.Models.Enums;

namespace Vigia.API.Contracts;

public interface IDeviceCommandsService
{
    Task<bool> SendCommandAsync(Guid deviceId, Guid userId, DeviceCommandDTO deviceCommand);
}