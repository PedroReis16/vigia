using Vigia.Cache.Services;
using Vigia.Models.Entities;

namespace Vigia.Database.Cache;

internal class RepositoryCache<TEntity>(IInMemoryCacheService cacheService) : IRepositoryCache<TEntity> where TEntity : BaseEntity
{
    protected IInMemoryCacheService _cacheService = cacheService;
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
        return _cacheService.Get(RepositoryCache<TEntity>.GetCacheKey(key)) as TEntity;
    }

}