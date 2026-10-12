using Microsoft.EntityFrameworkCore;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;

namespace Vigia.Database.EFDao;

internal class FallAlertEpisodeDao(VigiaDbContext context) : IFallAlertEpisodeDao
{
    private readonly VigiaDbContext _context = context;

    public Task<FallAlertEpisode?> FindAsync(Guid id, CancellationToken cancellationToken = default)
    {
        return _context.FallAlertEpisodes
            .FirstOrDefaultAsync(e => e.Id == id && e.DeletedAt == null, cancellationToken);
    }

    public Task<FallAlertEpisode?> FindActiveByDeviceAsync(Guid deviceId, CancellationToken cancellationToken = default)
    {
        return _context.FallAlertEpisodes
            .FirstOrDefaultAsync(
                e => e.DeviceId == deviceId
                    && e.DeletedAt == null
                    && e.Status == FallAlertEpisodeStatus.Active,
                cancellationToken);
    }

    public Task<List<FallAlertEpisode>> ListActiveByDeviceAsync(Guid deviceId, CancellationToken cancellationToken = default)
    {
        return _context.FallAlertEpisodes
            .Where(e => e.DeviceId == deviceId
                && e.DeletedAt == null
                && e.Status == FallAlertEpisodeStatus.Active)
            .ToListAsync(cancellationToken);
    }

    public async Task AddAsync(FallAlertEpisode episode, CancellationToken cancellationToken = default)
    {
        _context.FallAlertEpisodes.Add(episode);
        await _context.SaveChangesAsync(cancellationToken);
    }

    public async Task UpdateAsync(FallAlertEpisode episode, CancellationToken cancellationToken = default)
    {
        episode.UpdatedAt = DateTime.UtcNow;
        _context.FallAlertEpisodes.Update(episode);
        await _context.SaveChangesAsync(cancellationToken);
    }

    public Task<List<FallAlertEpisode>> ListDueForRetryAsync(DateTime utcNow, CancellationToken cancellationToken = default)
    {
        return _context.FallAlertEpisodes
            .Include(e => e.Device)
            .Where(e => e.DeletedAt == null
                && e.Status == FallAlertEpisodeStatus.Active
                && e.NextRetryAt != null
                && e.NextRetryAt <= utcNow)
            .OrderBy(e => e.NextRetryAt)
            .ToListAsync(cancellationToken);
    }
}
