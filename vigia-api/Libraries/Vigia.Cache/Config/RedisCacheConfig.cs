namespace Vigia.Cache.Config;

public class RedisCacheConfig
{
    public const string REDIS_CONFIG_SECTION = "RedisCaching";
    public const string REDIS_MAX_AGE = "MaxAge";
    public const string REDIS_INSTANCE_NAME = "InstanceName";
    public const string REDIS_CONNECTION_NAME = "Redis";

    public string ConnectionString { get; private set; } = "localhost:6379";
    public string InstanceName { get; private set; } = "vigia:";
    public int ExpirationInSeconds { get; private set; } = 3600;

    public RedisCacheConfig()
    {
    }

    public RedisCacheConfig(string connectionString, int expirationInSeconds, string? instanceName = null)
    {
        ConnectionString = string.IsNullOrWhiteSpace(connectionString)
            ? "localhost:6379"
            : connectionString;
        ExpirationInSeconds = expirationInSeconds > 0 ? expirationInSeconds : 3600;
        InstanceName = string.IsNullOrWhiteSpace(instanceName) ? "vigia:" : instanceName;
    }
}
