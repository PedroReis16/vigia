using Vigia.API.Models.DTOs.Notifications;

namespace Vigia.API.Contracts;

public interface INotificationInboxService
{
    Task<NotificationListDTO> ListAsync(Guid userId, int? skip = null, int? take = null);

    Task MarkReadAsync(Guid userId, Guid notificationId);

    Task MarkAllReadAsync(Guid userId);

    Task AcknowledgeDeviceAlertsAsync(Guid userId, Guid deviceId);
}
