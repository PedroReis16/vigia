using Vigia.Fiware.Models.SubscriptionDTOs;

namespace Vigia.Fiware.Services;

public static class OrionSubscriptionNotificationFactory
{
    public static OrionSubscriptionNotificationDTO Create(
        string url,
        IReadOnlyList<string> attrs,
        string attrsFormat,
        string? authorizationHeader)
    {
        OrionSubscriptionNotificationDTO notification = new()
        {
            Attrs = attrs.ToList(),
            AttrsFormat = attrsFormat,
        };

        if (string.IsNullOrWhiteSpace(authorizationHeader))
        {
            notification.Http = new OrionSubscriptionHttpDTO { Url = url };
            return notification;
        }

        notification.HttpCustom = new OrionSubscriptionHttpCustomDTO
        {
            Url = url,
            Headers = new Dictionary<string, string>(StringComparer.Ordinal)
            {
                ["Authorization"] = authorizationHeader,
            },
        };
        return notification;
    }
}
