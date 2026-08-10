namespace Vigia.Cache.Config;

public class InMemoryCacheConfig
{
    public const string IN_MEMORY_CONFIG_SECTION = "InMemoryCaching";
    public const string IN_MEMORY_MAX_AGE = "MaxAge";

    public int ExpirationInSeconds { get; private set; }

    public InMemoryCacheConfig()
    {

    }

    public InMemoryCacheConfig(int expirationInSeconds)
    {
        ExpirationInSeconds = expirationInSeconds > 0 ? expirationInSeconds : 3600;
    }
}