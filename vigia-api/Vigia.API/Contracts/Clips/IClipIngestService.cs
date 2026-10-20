using Vigia.API.Models.DTOs.Devices;
using Vigia.Cloud.Contracts;

namespace Vigia.API.Contracts.Clips;

public interface IClipIngestService
{
    Task OpenSessionAsync(Guid deviceId, OpenClipSessionDTO session, CancellationToken cancellationToken = default);
    Task SaveFrameAsync(Guid deviceId, Guid clipId, int index, Stream png, CancellationToken cancellationToken = default);
    Task<List<DeviceClipDTO>> ListAsync(Guid deviceId, Guid userId, CancellationToken cancellationToken = default);
    Task<long?> GetVideoLengthAsync(Guid deviceId, Guid clipId, CancellationToken cancellationToken = default);
    Task<CloudObjectRead?> OpenVideoAsync(Guid deviceId, Guid clipId, long? start, long? end, CancellationToken cancellationToken = default);
    Task<Stream?> OpenThumbnailAsync(Guid deviceId, Guid clipId, CancellationToken cancellationToken = default);
}
