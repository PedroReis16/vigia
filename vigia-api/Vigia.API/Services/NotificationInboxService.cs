using Microsoft.Extensions.Options;
using Vigia.API.Config;
using Vigia.API.Contracts;
using Vigia.API.Models.DTOs.Notifications;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.Services;

internal class NotificationInboxService(
    IUserNotificationDao notificationDao,
    IFallAlertEpisodeDao episodeDao,
    IDevicesDao devicesDao,
    IGroupDao groupDao,
    IOptions<AlertOptions> alertOptions) : INotificationInboxService
{
    private readonly IUserNotificationDao _notificationDao = notificationDao;
    private readonly IFallAlertEpisodeDao _episodeDao = episodeDao;
    private readonly IDevicesDao _devicesDao = devicesDao;
    private readonly IGroupDao _groupDao = groupDao;
    private readonly AlertOptions _alertOptions = alertOptions.Value;

    public async Task<NotificationListDTO> ListAsync(Guid userId, int? skip = null, int? take = null)
    {
        int pageSkip = Math.Max(0, skip ?? 0);
        int pageTake = Math.Clamp(take ?? _alertOptions.InboxPageSize, 1, 100);

        (List<UserNotification> items, int unreadCount) = await _notificationDao.ListByUserAsync(
            userId,
            pageSkip,
            pageTake);

        return new NotificationListDTO
        {
            UnreadCount = unreadCount,
            Items = items.Select(Map).ToList(),
        };
    }

    public async Task MarkReadAsync(Guid userId, Guid notificationId)
    {
        UserNotification? notification = await _notificationDao.FindForUserAsync(notificationId, userId);
        if (notification is null)
            throw new HttpResponseException(StatusCodes.Status404NotFound, "Notificação não encontrada", ErrorCodes.NOTIFICATION_NOT_FOUND);

        await _notificationDao.MarkReadAsync(notificationId, userId, DateTime.UtcNow);
    }

    public Task MarkAllReadAsync(Guid userId)
    {
        return _notificationDao.MarkAllReadAsync(userId, DateTime.UtcNow);
    }

    public async Task AcknowledgeDeviceAlertsAsync(Guid userId, Guid deviceId)
    {
        Device? device = await _devicesDao.FindAsync(deviceId);
        if (device is null)
            throw new HttpResponseException(StatusCodes.Status404NotFound, "Dispositivo não encontrado", ErrorCodes.DEVICE_NOT_FOUND);

        if (device.GroupId is null)
            return;

        if (!await _groupDao.IsUserInGroupAsync(device.GroupId.Value, userId))
            throw new HttpResponseException(StatusCodes.Status403Forbidden, "Usuário não é membro do grupo do dispositivo", ErrorCodes.NOT_GROUP_MEMBER);

        List<FallAlertEpisode> active = await _episodeDao.ListActiveByDeviceAsync(deviceId);
        if (active.Count == 0)
            return;

        DateTime now = DateTime.UtcNow;
        foreach (FallAlertEpisode episode in active)
        {
            episode.Status = FallAlertEpisodeStatus.Acknowledged;
            episode.AcknowledgedAt = now;
            episode.AcknowledgedByUserId = userId;
            episode.NextRetryAt = null;
            await _episodeDao.UpdateAsync(episode);
        }

        await _notificationDao.MarkReadByEpisodesAsync(
            userId,
            active.Select(e => e.Id),
            now);
    }

    private static UserNotificationDTO Map(UserNotification notification) => new()
    {
        Id = notification.Id,
        EpisodeId = notification.EpisodeId,
        DeviceId = notification.DeviceId,
        Type = notification.Type,
        Title = notification.Title,
        Body = notification.Body,
        CreatedAt = notification.CreatedAt,
        Read = notification.ReadAt is not null,
        ReadAt = notification.ReadAt,
    };
}
