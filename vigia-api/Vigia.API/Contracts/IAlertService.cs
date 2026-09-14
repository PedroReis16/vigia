using Vigia.API.Models.DTOs.Alerts;

namespace Vigia.API.Contracts;

public interface IAlertService
{
    Task HandleFallWebhookAsync(OrionAlertNotificationDTO notification);
}
