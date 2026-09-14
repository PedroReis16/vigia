using Vigia.Cache.Services;
using Vigia.Models.Entities;
using Vigia.Database.CacheContracts;

namespace Vigia.Database.Cache;

public class RepositoryCache<TEntity>(IRedisCacheService cacheService) : IRepositoryCache<TEntity> where TEntity : BaseEntity
{
    protected IRedisCacheService _cacheService = cacheService;
    private static string GetCacheKey(string key) => $"{typeof(TEntity).Name}-{key}";

    public virtual void AddEntity(TEntity entity)
    {
        _cacheService.Add(RepositoryCache<TEntity>.GetCacheKey(entity.Id.ToString()), entity);
    }

    public virtual void AddEntity(string key, TEntity entity)
    {
        _cacheService.Add(RepositoryCache<TEntity>.GetCacheKey(key), entity);
    }

    public void ClearAll()
    {
        _cacheService.Clear();
    }

    public virtual void RemoveEntity(params TEntity[] entities)
    {
        foreach (TEntity entity in entities)
        {
            _cacheService.Remove(RepositoryCache<TEntity>.GetCacheKey(entity.Id.ToString()));
        }
    }

    public virtual void RemoveEntity(string key)
    {
        _cacheService.Remove(RepositoryCache<TEntity>.GetCacheKey(key));
    }

    public virtual TEntity? GetEntity(string key)
    {
        return _cacheService.Get<TEntity>(RepositoryCache<TEntity>.GetCacheKey(key));
    }
}
