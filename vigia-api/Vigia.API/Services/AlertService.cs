using System.Text.Json;
using Microsoft.Extensions.Options;
using Vigia.API.Config;
using Vigia.API.Contracts;
using Vigia.API.Models.DTOs.Alerts;
using Vigia.Database.Contracts;
using Vigia.Fiware.Config;
using Vigia.Models.Entities;
using Vigia.Models.Enums;

namespace Vigia.API.Services;

internal class AlertService(
    ILogger<AlertService> logger,
    IOptionsSnapshot<SubscriptionSchemaOptions> subscriptionOptions,
    IOptions<AlertOptions> alertOptions,
    IDevicesDao devicesDao,
    IUserDao userDao,
    IUserPushTokenDao pushTokenDao,
    IFallAlertEpisodeDao episodeDao,
    IUserNotificationDao notificationDao,
    IPushNotificationService pushNotificationService) : IAlertService
{
    private const string OrionEntityPrefix = "urn:ngsi-ld:";
    private const string FallNotificationType = "fall";

    private readonly ILogger<AlertService> _logger = logger;
    private readonly SubscriptionSchemaOptions _subscriptions = subscriptionOptions.Value;
    private readonly AlertOptions _alertOptions = alertOptions.Value;
    private readonly IDevicesDao _devicesDao = devicesDao;
    private readonly IUserDao _userDao = userDao;
    private readonly IUserPushTokenDao _pushTokenDao = pushTokenDao;
    private readonly IFallAlertEpisodeDao _episodeDao = episodeDao;
    private readonly IUserNotificationDao _notificationDao = notificationDao;
    private readonly IPushNotificationService _pushNotificationService = pushNotificationService;

    public async Task HandleFallWebhookAsync(OrionAlertNotificationDTO notification)
    {
        if (notification.Data.Count == 0)
        {
            _logger.LogWarning(
                "Webhook Orion de alerta recebido sem entidades. Subscription={SubscriptionId}",
                notification.SubscriptionId);
            return;
        }

        List<SubscriptionDefinitionOptions> definitions = _subscriptions.GetSubscriptions();
        if (definitions.Count == 0)
        {
            _logger.LogWarning(
                "Webhook Orion recebido sem subscrições em Fiware:Subscriptions. Subscription={SubscriptionId}",
                notification.SubscriptionId);
            return;
        }

        foreach (OrionAlertEntityDTO entity in notification.Data)
        {
            if (!TryRecognizeAlert(entity, definitions, out string? matchedExpression, out string? matchedValue))
            {
                _logger.LogInformation(
                    "Webhook Orion ignorado: nenhuma condição de Fiware:Subscriptions satisfeita. Entity={EntityId}",
                    entity.Id);
                continue;
            }

            _logger.LogInformation(
                "Alerta reconhecido via webhook Orion. Entity={EntityId} Expression={Expression} Value={Value} Subscription={SubscriptionId}",
                entity.Id,
                matchedExpression,
                matchedValue,
                notification.SubscriptionId);

            await DeliverFallAlertAsync(entity.Id);
        }
    }

    private async Task DeliverFallAlertAsync(string entityId)
    {
        Device? device = await ResolveDeviceAsync(entityId);
        if (device is null)
        {
            _logger.LogWarning("Webhook Orion com entity id inválido ou dispositivo não encontrado: {EntityId}", entityId);
            return;
        }

        if (device.GroupId is null || device.Group is null)
        {
            _logger.LogInformation(
                "Alerta de queda ignorado: dispositivo {DeviceId} sem grupo vinculado.",
                device.Id);
            return;
        }

        FallAlertEpisode? active = await _episodeDao.FindActiveByDeviceAsync(device.Id);
        if (active is not null)
        {
            _logger.LogInformation(
                "Alerta de queda ignorado: episódio Active já existe. Device={DeviceId} Episode={EpisodeId}",
                device.Id,
                active.Id);
            return;
        }

        List<User> groupUsers = await _userDao.GetUsersByGroupAsync(device.Group.Id);
        if (groupUsers.Count == 0)
        {
            _logger.LogWarning(
                "Alerta de queda ignorado: grupo {GroupId} sem usuários.",
                device.Group.Id);
            return;
        }

        DateTime now = DateTime.UtcNow;
        string displayName = string.IsNullOrWhiteSpace(device.Nickname) ? device.Name : device.Nickname!;
        string title = "Alerta de queda";
        string body = $"Queda detectada em {displayName}";

        FallAlertEpisode episode = new()
        {
            DeviceId = device.Id,
            GroupId = device.Group.Id,
            Status = FallAlertEpisodeStatus.Active,
            FirstDetectedAt = now,
            LastNotifiedAt = now,
            NotifyCount = 1,
            NextRetryAt = now.AddSeconds(Math.Max(1, _alertOptions.RetryIntervalSeconds)),
        };

        await _episodeDao.AddAsync(episode);

        List<UserNotification> inboxItems = groupUsers.Select(user => new UserNotification
        {
            UserId = user.Id,
            EpisodeId = episode.Id,
            DeviceId = device.Id,
            Type = FallNotificationType,
            Title = title,
            Body = body,
            CreatedAt = now,
        }).ToList();

        await _notificationDao.AddRangeAsync(inboxItems);

        List<string> tokens = await _pushTokenDao.GetTokensByUserIdsAsync(groupUsers.Select(u => u.Id));
        if (tokens.Count == 0)
        {
            _logger.LogWarning(
                "Episódio de queda criado sem tokens FCM ativos. Device={DeviceId} Episode={EpisodeId} Group={GroupId}",
                device.Id,
                episode.Id,
                device.Group.Id);
            return;
        }

        PushNotificationResult result = await _pushNotificationService.SendFallAlertAsync(
            new FallAlertPushRequest(episode.Id, device.Id, device.Name, device.Nickname, tokens));

        if (result.InvalidTokens.Count > 0)
            await _pushTokenDao.DeleteTokensAsync(result.InvalidTokens);
    }

    private async Task<Device?> ResolveDeviceAsync(string entityId)
    {
        if (string.IsNullOrWhiteSpace(entityId))
            return null;

        string id = entityId.Trim();

        const string sensorPrefix = "Sensor:";
        if (id.StartsWith(sensorPrefix, StringComparison.OrdinalIgnoreCase))
        {
            string maybeGuid = id[sensorPrefix.Length..];
            if (Guid.TryParse(maybeGuid, out Guid shadowDeviceId))
                return await _devicesDao.FindAsync(shadowDeviceId);
        }

        if (!TryResolveDeviceName(id, out string deviceName))
            return null;

        Device? byName = await _devicesDao.FindByNameAsync(deviceName);
        if (byName is not null)
            return byName;

        if (Guid.TryParse(deviceName, out Guid asGuid))
            return await _devicesDao.FindAsync(asGuid);

        return null;
    }

    private static bool TryResolveDeviceName(string entityId, out string deviceName)
    {
        deviceName = string.Empty;
        if (string.IsNullOrWhiteSpace(entityId))
            return false;

        if (entityId.StartsWith(OrionEntityPrefix, StringComparison.OrdinalIgnoreCase))
        {
            deviceName = entityId[OrionEntityPrefix.Length..];
            return !string.IsNullOrWhiteSpace(deviceName);
        }

        deviceName = entityId;
        return true;
    }

    private static bool TryRecognizeAlert(
        OrionAlertEntityDTO entity,
        IEnumerable<SubscriptionDefinitionOptions> definitions,
        out string? matchedExpression,
        out string? matchedValue)
    {
        matchedExpression = null;
        matchedValue = null;

        foreach (SubscriptionDefinitionOptions definition in definitions)
        {
            foreach (string attr in definition.GetConditionAttrs())
            {
                if (!TryGetAttributeValue(entity, attr, out string? value))
                    continue;

                string? expression = definition.GetExpression();
                if (expression is not null && !ExpressionMatches(expression, attr, value))
                    continue;

                matchedExpression = expression ?? attr;
                matchedValue = value;
                return true;
            }
        }

        return false;
    }

    private static bool ExpressionMatches(string expression, string attrName, string? value)
    {
        int separator = expression.IndexOf("==", StringComparison.Ordinal);
        if (separator <= 0)
            return false;

        string expectedAttr = expression[..separator].Trim();
        string expectedValue = expression[(separator + 2)..].Trim();

        return string.Equals(expectedAttr, attrName, StringComparison.Ordinal)
            && string.Equals(expectedValue, value, StringComparison.OrdinalIgnoreCase);
    }

    private static bool TryGetAttributeValue(OrionAlertEntityDTO entity, string attrName, out string? value)
    {
        value = null;
        if (!entity.Attributes.TryGetValue(attrName, out JsonElement attribute))
            return false;

        value = attribute.ValueKind switch
        {
            JsonValueKind.String => attribute.GetString(),
            JsonValueKind.True => bool.TrueString,
            JsonValueKind.False => bool.FalseString,
            JsonValueKind.Number => attribute.ToString(),
            JsonValueKind.Object when attribute.TryGetProperty("value", out JsonElement nested) =>
                nested.ValueKind == JsonValueKind.String ? nested.GetString() : nested.ToString(),
            _ => attribute.ToString()
        };

        return !string.IsNullOrWhiteSpace(value);
    }
}
