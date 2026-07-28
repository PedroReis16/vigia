using Vigia.Models.Entities;

namespace Vigia.Database.Cache;

public interface IRepositoryCache<TEntity> where TEntity : BaseEntity
{
    void AddEntity(TEntity entity);
    void AddEntity(string key, TEntity entity);
    TEntity? GetEntity(string key);
    void RemoveEntity(string key);
    void RemoveEntity(params TEntity[] entities);
    void ClearAll();
}