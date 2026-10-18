using Vigia.API.Models.DTOs.Devices;

namespace Vigia.API.Contracts.Devices;

public interface IDeviceCommandsService
{
    Task<bool> SendCommandAsync(Guid deviceId, Guid userId, DeviceCommandDTO deviceCommand);

    /// <summary>
    /// Envia START_STREAMING sem checagem de ACL de usuário (caller confiável: MediaMTX runOnDemand).
    /// </summary>
    Task<bool> SendDemandStartStreamingAsync(Guid deviceId);

    /// <summary>
    /// Envia STOP_STREAMING sem checagem de ACL de usuário (caller confiável: MediaMTX runOnUnDemand).
    /// </summary>
    Task<bool> SendUndemandStopStreamingAsync(Guid deviceId);
}