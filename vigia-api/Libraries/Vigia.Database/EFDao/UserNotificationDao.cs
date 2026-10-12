using Microsoft.EntityFrameworkCore;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;

namespace Vigia.Database.EFDao;

internal class UserNotificationDao(VigiaDbContext context) : IUserNotificationDao
{
    private readonly VigiaDbContext _context = context;

    public async Task AddRangeAsync(IEnumerable<UserNotification> notifications, CancellationToken cancellationToken = default)
    {
        _context.UserNotifications.AddRange(notifications);
        await _context.SaveChangesAsync(cancellationToken);
    }

    public async Task<(List<UserNotification> Items, int UnreadCount)> ListByUserAsync(
        Guid userId,
        int skip,
        int take,
        CancellationToken cancellationToken = default)
    {
        IQueryable<UserNotification> query = _context.UserNotifications
            .AsNoTracking()
            .Where(n => n.UserId == userId && n.DeletedAt == null);

        int unreadCount = await query.CountAsync(n => n.ReadAt == null, cancellationToken);

        List<UserNotification> items = await query
            .OrderByDescending(n => n.CreatedAt)
            .Skip(skip)
            .Take(take)
            .ToListAsync(cancellationToken);

        return (items, unreadCount);
    }

    public Task<UserNotification?> FindForUserAsync(Guid notificationId, Guid userId, CancellationToken cancellationToken = default)
    {
        return _context.UserNotifications
            .FirstOrDefaultAsync(
                n => n.Id == notificationId && n.UserId == userId && n.DeletedAt == null,
                cancellationToken);
    }

    public async Task MarkReadAsync(Guid notificationId, Guid userId, DateTime readAtUtc, CancellationToken cancellationToken = default)
    {
        UserNotification? notification = await FindForUserAsync(notificationId, userId, cancellationToken);
        if (notification is null || notification.ReadAt is not null)
            return;

        notification.ReadAt = readAtUtc;
        notification.UpdatedAt = readAtUtc;
        await _context.SaveChangesAsync(cancellationToken);
    }

    public async Task MarkAllReadAsync(Guid userId, DateTime readAtUtc, CancellationToken cancellationToken = default)
    {
        List<UserNotification> unread = await _context.UserNotifications
            .Where(n => n.UserId == userId && n.DeletedAt == null && n.ReadAt == null)
            .ToListAsync(cancellationToken);

        foreach (UserNotification notification in unread)
        {
            notification.ReadAt = readAtUtc;
            notification.UpdatedAt = readAtUtc;
        }

        if (unread.Count > 0)
            await _context.SaveChangesAsync(cancellationToken);
    }

    public async Task MarkReadByEpisodesAsync(
        Guid userId,
        IEnumerable<Guid> episodeIds,
        DateTime readAtUtc,
        CancellationToken cancellationToken = default)
    {
        List<Guid> ids = episodeIds.Distinct().ToList();
        if (ids.Count == 0)
            return;

        List<UserNotification> unread = await _context.UserNotifications
            .Where(n => n.UserId == userId
                && n.DeletedAt == null
                && n.ReadAt == null
                && ids.Contains(n.EpisodeId))
            .ToListAsync(cancellationToken);

        foreach (UserNotification notification in unread)
        {
            notification.ReadAt = readAtUtc;
            notification.UpdatedAt = readAtUtc;
        }

        if (unread.Count > 0)
            await _context.SaveChangesAsync(cancellationToken);
    }
}
