namespace Vigia.AMQP.Configuration;

public static class ExchangeNames
{
    private const string ExchangeTypeDirect = "direct";
    private const string ExchangeTypeTopic = "topic";
    private const string ExchangeTypeFanout = "fanout";
    private const string ExchangeTypeHeaders = "headers";

    public const string UserSync = "vigia.users.direct_exchange";
    public const string UserSyncDlq = "vigia.users.dlq.direct_exchange";

    private static readonly Dictionary<string, string> ExchangeTypes = new(StringComparer.OrdinalIgnoreCase)
    {
        [UserSync] = ExchangeTypeDirect,
        [UserSyncDlq] = ExchangeTypeDirect,
    };

    public static string GetExchangeType(string exchangeName)
    {

        if (ExchangeTypes.TryGetValue(exchangeName, out string? exchangeType))
            return exchangeType;

        if (exchangeName.Contains("direct_exchange", StringComparison.OrdinalIgnoreCase))
            return ExchangeTypeDirect;

        if (exchangeName.Contains("topic_exchange", StringComparison.OrdinalIgnoreCase))
            return ExchangeTypeTopic;

        if (exchangeName.Contains("fanout_exchange", StringComparison.OrdinalIgnoreCase))
            return ExchangeTypeFanout;

        if (exchangeName.Contains("headers_exchange", StringComparison.OrdinalIgnoreCase))
            return ExchangeTypeHeaders;

        // Fallback seguro para a maioria dos casos neste projeto
        return ExchangeTypeTopic;
    }
}