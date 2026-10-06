using Vigia.Models.Entities;

namespace Vigia.Database.Contracts;

public interface IDeviceClipDao
{
    Task<DeviceClip?> FindAsync(Guid id, CancellationToken cancellationToken = default);
    Task AddAsync(DeviceClip clip, CancellationToken cancellationToken = default);
    Task<bool> TryMarkAssemblingAsync(Guid id, CancellationToken cancellationToken = default);
    Task MarkReadyAsync(Guid id, string objectKey, CancellationToken cancellationToken = default);
    Task MarkFailedAsync(Guid id, CancellationToken cancellationToken = default);
    Task<List<DeviceClip>> ListByDeviceAsync(Guid deviceId, CancellationToken cancellationToken = default);
    Task<List<DeviceClip>> ListReceivingOlderThanAsync(DateTime createdBeforeUtc, CancellationToken cancellationToken = default);
    Task<List<DeviceClip>> ListAssemblingAsync(CancellationToken cancellationToken = default);
}
