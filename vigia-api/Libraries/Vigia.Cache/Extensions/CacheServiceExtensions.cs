using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Vigia.Cache.Config;
using Vigia.Cache.Services;

namespace Vigia.Cache.Extensions;

public static class CacheServiceExtensions
{
    public static IServiceCollection AddInMemoryCache(this IServiceCollection services, IConfiguration configuration)
    {
        return services.AddMemoryCache()
            .AddSingleton(GetCacheConfig(configuration))
            .AddSingleton<IInMemoryCacheService, InMemoryCacheService>();
    }

    private static InMemoryCacheConfig GetCacheConfig(IConfiguration configuration)
    {
        _ = int.TryParse(configuration
            .GetSection(InMemoryCacheConfig.IN_MEMORY_CONFIG_SECTION)
            .GetSection(InMemoryCacheConfig.IN_MEMORY_MAX_AGE)
            .Value, out int maxAge);
        return new InMemoryCacheConfig(maxAge);
    }
}