using Microsoft.Extensions.Caching.Memory;
using Microsoft.Extensions.Primitives;
using Vigia.Cache.Config;

namespace Vigia.Cache.Services;

public class InMemoryCacheService(InMemoryCacheConfig config, IMemoryCache memoryCache) : IInMemoryCacheService
{
    protected readonly InMemoryCacheConfig _config = config;
    protected readonly IMemoryCache _memoryCache = memoryCache;
    private CancellationTokenSource _resetCacheSource = new();

    public virtual void Add(string key, object value)
    {
        MemoryCacheEntryOptions cacheEntryOptions = new MemoryCacheEntryOptions()
            .SetAbsoluteExpiration(TimeSpan.FromSeconds(_config.ExpirationInSeconds));

        _ = cacheEntryOptions.AddExpirationToken(new CancellationChangeToken(_resetCacheSource.Token));

        _ = _memoryCache.Set(key.ToUpperInvariant(), value, cacheEntryOptions);
    }

    public virtual object? Get(string key)
    {
        if (_memoryCache.TryGetValue(key.ToUpperInvariant(), out object? value))
            return value;
        else
            return null;
    }

    public virtual void Remove(string key)
    {
        _memoryCache.Remove(key.ToUpperInvariant());
    }

    public virtual void Clear()
    {
        if (_resetCacheSource != null && !_resetCacheSource.IsCancellationRequested && _resetCacheSource.Token.CanBeCanceled)
        {
            _resetCacheSource.Cancel();
            _resetCacheSource.Dispose();
        }
        _resetCacheSource = new CancellationTokenSource();
    }
}