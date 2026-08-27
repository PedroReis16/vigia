using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using StackExchange.Redis;
using Vigia.Cache.Config;
using Vigia.Cache.Services;

namespace Vigia.Cache.Extensions;

public static class CacheServiceExtensions
{
    public static IServiceCollection AddInMemoryCache(this IServiceCollection services, IConfiguration configuration)
    {
        return services.AddMemoryCache()
            .AddSingleton(GetInMemoryCacheConfig(configuration))
            .AddSingleton<IInMemoryCacheService, InMemoryCacheService>();
    }

    public static IServiceCollection AddRedisCache(this IServiceCollection services, IConfiguration configuration)
    {
        RedisCacheConfig config = GetRedisCacheConfig(configuration);
        ConnectionMultiplexer multiplexer = ConnectionMultiplexer.Connect(config.ConnectionString);

        return services
            .AddSingleton(config)
            .AddSingleton<IConnectionMultiplexer>(multiplexer)
            .AddSingleton<IRedisCacheService, RedisCacheService>();
    }

    private static InMemoryCacheConfig GetInMemoryCacheConfig(IConfiguration configuration)
    {
        _ = int.TryParse(configuration
            .GetSection(InMemoryCacheConfig.IN_MEMORY_CONFIG_SECTION)
            .GetSection(InMemoryCacheConfig.IN_MEMORY_MAX_AGE)
            .Value, out int maxAge);
        return new InMemoryCacheConfig(maxAge);
    }

    private static RedisCacheConfig GetRedisCacheConfig(IConfiguration configuration)
    {
        string? connectionString = configuration.GetConnectionString(RedisCacheConfig.REDIS_CONNECTION_NAME);

        _ = int.TryParse(configuration
            .GetSection(RedisCacheConfig.REDIS_CONFIG_SECTION)
            .GetSection(RedisCacheConfig.REDIS_MAX_AGE)
            .Value, out int maxAge);

        string? instanceName = configuration
            .GetSection(RedisCacheConfig.REDIS_CONFIG_SECTION)
            .GetSection(RedisCacheConfig.REDIS_INSTANCE_NAME)
            .Value;

        return new RedisCacheConfig(connectionString ?? string.Empty, maxAge, instanceName);
    }
}