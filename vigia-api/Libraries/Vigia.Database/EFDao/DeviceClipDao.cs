using Microsoft.EntityFrameworkCore;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;

namespace Vigia.Database.EFDao;

internal class DeviceClipDao(VigiaDbContext context) : IDeviceClipDao
{
    private readonly VigiaDbContext _context = context;

    public Task<DeviceClip?> FindAsync(Guid id, CancellationToken cancellationToken = default)
    {
        return _context.DeviceClips
            .FirstOrDefaultAsync(clip => clip.Id == id && clip.DeletedAt == null, cancellationToken);
    }

    public async Task AddAsync(DeviceClip clip, CancellationToken cancellationToken = default)
    {
        _context.DeviceClips.Add(clip);
        await _context.SaveChangesAsync(cancellationToken);
    }

    public async Task<bool> TryMarkAssemblingAsync(Guid id, CancellationToken cancellationToken = default)
    {
        DeviceClip? clip = await _context.DeviceClips
            .FirstOrDefaultAsync(
                item => item.Id == id && item.DeletedAt == null && item.Status == ClipStatus.Receiving,
                cancellationToken);

        if (clip == null)
            return false;

        clip.Status = ClipStatus.Assembling;
        clip.UpdatedAt = DateTime.UtcNow;
        await _context.SaveChangesAsync(cancellationToken);
        return true;
    }

    public async Task MarkReadyAsync(Guid id, string objectKey, CancellationToken cancellationToken = default)
    {
        DeviceClip? clip = await _context.DeviceClips
            .FirstOrDefaultAsync(item => item.Id == id && item.DeletedAt == null, cancellationToken);

        if (clip == null)
            return;

        clip.Status = ClipStatus.Ready;
        clip.ObjectKey = objectKey;
        clip.UpdatedAt = DateTime.UtcNow;
        await _context.SaveChangesAsync(cancellationToken);
    }

    public async Task MarkFailedAsync(Guid id, CancellationToken cancellationToken = default)
    {
        DeviceClip? clip = await _context.DeviceClips
            .FirstOrDefaultAsync(item => item.Id == id && item.DeletedAt == null, cancellationToken);

        if (clip == null || clip.Status == ClipStatus.Ready)
            return;

        clip.Status = ClipStatus.Failed;
        clip.UpdatedAt = DateTime.UtcNow;
        await _context.SaveChangesAsync(cancellationToken);
    }

    public Task<List<DeviceClip>> ListByDeviceAsync(Guid deviceId, CancellationToken cancellationToken = default)
    {
        return _context.DeviceClips
            .AsNoTracking()
            .Where(clip => clip.DeviceId == deviceId && clip.DeletedAt == null)
            .OrderByDescending(clip => clip.CreatedAt)
            .ToListAsync(cancellationToken);
    }

    public Task<List<DeviceClip>> ListReceivingOlderThanAsync(DateTime createdBeforeUtc, CancellationToken cancellationToken = default)
    {
        return _context.DeviceClips
            .Where(clip =>
                clip.DeletedAt == null &&
                clip.Status == ClipStatus.Receiving &&
                clip.CreatedAt < createdBeforeUtc)
            .ToListAsync(cancellationToken);
    }

    public Task<List<DeviceClip>> ListAssemblingAsync(CancellationToken cancellationToken = default)
    {
        return _context.DeviceClips
            .Where(clip => clip.DeletedAt == null && clip.Status == ClipStatus.Assembling)
            .ToListAsync(cancellationToken);
    }
}
