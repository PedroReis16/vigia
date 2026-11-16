using Vigia.Models.Entities;
using Vigia.Models.Enums;

namespace Vigia.Database.Contracts;

public interface IFallAlertEpisodeDao
{
    Task<FallAlertEpisode?> FindActiveByDeviceAsync(
        Guid deviceId,
        AlertEpisodeKind kind = AlertEpisodeKind.Fall,
        CancellationToken cancellationToken = default);

    Task AddAsync(FallAlertEpisode episode, CancellationToken cancellationToken = default);

    Task UpdateAsync(FallAlertEpisode episode, CancellationToken cancellationToken = default);

    Task<List<FallAlertEpisode>> ListDueForRetryAsync(DateTime utcNow, CancellationToken cancellationToken = default);

    Task<List<FallAlertEpisode>> ListActiveByDeviceAsync(
        Guid deviceId,
        AlertEpisodeKind kind = AlertEpisodeKind.Fall,
        CancellationToken cancellationToken = default);

    Task<FallAlertEpisode?> FindAsync(Guid id, CancellationToken cancellationToken = default);
}
