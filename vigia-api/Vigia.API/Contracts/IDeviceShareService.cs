using Vigia.API.Models.DTOs.Devices;

namespace Vigia.API.Contracts;

public interface IDeviceShareService
{
    Task<DeviceShareInviteDTO> GenerateInviteAsync(Guid deviceId, Guid userId);
    Task AcceptInviteAsync(string token, Guid userId);
}
