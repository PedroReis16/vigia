using Microsoft.Extensions.Caching.Memory;
using Microsoft.Extensions.Primitives;
using Vigia.Cache.Config;

namespace Vigia.Cache.Services;

public class InMemoryCacheService(InMemoryCacheConfig config, IMemoryCache memoryCache) : IInMemoryCacheService
{
    protected readonly InMemoryCacheConfig Config = config;
    protected readonly IMemoryCache MemoryCache = memoryCache;
    protected CancellationTokenSource ResetCacheSource = new();

    public virtual void Add(string key, object value)
    {
        MemoryCacheEntryOptions cacheEntryOptions = new MemoryCacheEntryOptions()
            .SetAbsoluteExpiration(TimeSpan.FromSeconds(Config.ExpirationInSeconds));

        _ = cacheEntryOptions.AddExpirationToken(new CancellationChangeToken(ResetCacheSource.Token));

        _ = MemoryCache.Set(key.ToUpperInvariant(), value, cacheEntryOptions);
    }

    public virtual object? Get(string key)
    {
        if (MemoryCache.TryGetValue(key.ToUpperInvariant(), out object? value))
            return value;
        else
            return null;
    }

    public virtual void Remove(string key)
    {
        MemoryCache.Remove(key.ToUpperInvariant());
    }

    public virtual void Clear()
    {
        if (ResetCacheSource != null && !ResetCacheSource.IsCancellationRequested && ResetCacheSource.Token.CanBeCanceled)
        {
            ResetCacheSource.Cancel();
            ResetCacheSource.Dispose();
        }
        ResetCacheSource = new CancellationTokenSource();
    }
}