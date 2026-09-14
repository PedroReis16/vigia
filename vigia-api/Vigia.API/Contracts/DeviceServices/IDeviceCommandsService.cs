using Vigia.API.Models.DTOs.Devices;

namespace Vigia.API.Contracts.Devices;

public interface IDeviceCommandsService
{
    Task<bool> SendCommandAsync(Guid deviceId, Guid userId, DeviceCommandDTO deviceCommand);

    /// <summary>
    /// Envia STOP_STREAMING sem checagem de ACL de usuário (caller confiável: MediaMTX).
    /// </summary>
    Task<bool> SendUndemandStopStreamingAsync(Guid deviceId);
}