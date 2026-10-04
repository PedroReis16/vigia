using Vigia.API.Models.DTOs.Devices;

namespace Vigia.API.Contracts.Clips;

public interface IClipIngestService
{
    Task OpenSessionAsync(Guid deviceId, OpenClipSessionDTO session, CancellationToken cancellationToken = default);
    Task SaveFrameAsync(Guid deviceId, Guid clipId, int index, Stream png, CancellationToken cancellationToken = default);
    Task<List<DeviceClipDTO>> ListAsync(Guid deviceId, CancellationToken cancellationToken = default);
    Task<Stream?> OpenVideoAsync(Guid deviceId, Guid clipId, CancellationToken cancellationToken = default);
}
