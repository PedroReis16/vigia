namespace Vigia.Fiware.Config;

/// <summary>
/// Subscrições Orion carregadas de <c>Fiware:Subscriptions</c> no appsettings.
/// </summary>
public class SubscriptionSchemaOptions
{
    public const string SectionName = "Fiware";

    public List<SubscriptionDefinitionOptions> Subscriptions { get; set; } = [];

    public List<SubscriptionDefinitionOptions> GetSubscriptions() =>
        Subscriptions
            .Where(IsValid)
            .ToList();

    private static bool IsValid(SubscriptionDefinitionOptions subscription) =>
        !string.IsNullOrWhiteSpace(subscription.Notification.Url)
        && subscription.GetConditionAttrs().Count > 0;
}

public class SubscriptionDefinitionOptions
{
    public string Description { get; set; } = string.Empty;

    public SubscriptionConditionOptions Condition { get; set; } = new();

    public SubscriptionNotificationOptions Notification { get; set; } = new();

    public List<string> GetConditionAttrs() => NormalizeAttrs(Condition.Attrs);

    public List<string> GetNotificationAttrs()
    {
        List<string> attrs = NormalizeAttrs(Notification.Attrs);
        return attrs.Count > 0 ? attrs : GetConditionAttrs();
    }

    public string? GetExpression() =>
        string.IsNullOrWhiteSpace(Condition.Expression) ? null : Condition.Expression.Trim();

    public string GetAttrsFormat() =>
        string.IsNullOrWhiteSpace(Notification.AttrsFormat)
            ? "normalized"
            : Notification.AttrsFormat.Trim();

    public string FormatDescription(string entityName, string entityType)
    {
        if (string.IsNullOrWhiteSpace(Description))
            return $"{entityType} subscription";

        return Description
            .Replace("{entityName}", entityName, StringComparison.Ordinal)
            .Replace("{entityType}", entityType, StringComparison.Ordinal);
    }

    private static List<string> NormalizeAttrs(IEnumerable<string> attrs) =>
        attrs
            .Where(attr => !string.IsNullOrWhiteSpace(attr))
            .Select(attr => attr.Trim())
            .Distinct(StringComparer.Ordinal)
            .OrderBy(attr => attr, StringComparer.Ordinal)
            .ToList();
}

public class SubscriptionConditionOptions
{
    public List<string> Attrs { get; set; } = [];

    public string? Expression { get; set; }
}

public class SubscriptionNotificationOptions
{
    public string Url { get; set; } = string.Empty;

    public List<string> Attrs { get; set; } = [];

    public string AttrsFormat { get; set; } = "normalized";
}
