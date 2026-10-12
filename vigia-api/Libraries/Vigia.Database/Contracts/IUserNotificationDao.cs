using Vigia.Models.Entities;

namespace Vigia.Database.Contracts;

public interface IUserNotificationDao
{
    Task AddRangeAsync(IEnumerable<UserNotification> notifications, CancellationToken cancellationToken = default);

    Task<(List<UserNotification> Items, int UnreadCount)> ListByUserAsync(
        Guid userId,
        int skip,
        int take,
        CancellationToken cancellationToken = default);

    Task<UserNotification?> FindForUserAsync(Guid notificationId, Guid userId, CancellationToken cancellationToken = default);

    Task MarkReadAsync(Guid notificationId, Guid userId, DateTime readAtUtc, CancellationToken cancellationToken = default);

    Task MarkAllReadAsync(Guid userId, DateTime readAtUtc, CancellationToken cancellationToken = default);

    Task MarkReadByEpisodesAsync(
        Guid userId,
        IEnumerable<Guid> episodeIds,
        DateTime readAtUtc,
        CancellationToken cancellationToken = default);
}
