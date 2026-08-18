using System.Text.Json;
using Microsoft.Extensions.Options;
using Vigia.API.Contracts;
using Vigia.API.Models.DTOs.Alerts;
using Vigia.Fiware.Config;

namespace Vigia.API.Services;

internal class AlertService(
    ILogger<AlertService> logger,
    IOptionsSnapshot<SubscriptionSchemaOptions> subscriptionOptions) : IAlertService
{
    private readonly ILogger<AlertService> _logger = logger;
    private readonly SubscriptionSchemaOptions _subscriptions = subscriptionOptions.Value;

    public Task HandleFallWebhookAsync(OrionAlertNotificationDTO notification)
    {
        if (notification.Data.Count == 0)
        {
            _logger.LogWarning(
                "Webhook Orion de alerta recebido sem entidades. Subscription={SubscriptionId}",
                notification.SubscriptionId);
            return Task.CompletedTask;
        }

        List<SubscriptionDefinitionOptions> definitions = _subscriptions.GetSubscriptions();
        if (definitions.Count == 0)
        {
            _logger.LogWarning(
                "Webhook Orion recebido sem subscrições em Fiware:Subscriptions. Subscription={SubscriptionId}",
                notification.SubscriptionId);
            return Task.CompletedTask;
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
        }

        return Task.CompletedTask;
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
