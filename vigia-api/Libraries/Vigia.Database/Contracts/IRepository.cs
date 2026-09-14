using Vigia.Models.Entities;

namespace Vigia.Database.Contracts;

public interface IRepository<TEntity> where TEntity : BaseEntity
{
    /// <summary>
    /// Get all entities async
    /// </summary>
    /// <returns>Entities list</returns>
    Task<List<TEntity>> AllAsync(bool track = false);

    /// <summary>
    /// Get an entity async by its primary key
    /// </summary>
    /// <param name="key">Primary key</param>
    /// <returns>Entity</returns>
    Task<TEntity?> FindAsync(object key, bool track = false);

    /// <summary>
    /// Insert one or many entities async
    /// </summary>
    /// <param name="obj">Entities</param>
    /// <returns>Entities affected count</returns>
    Task<int> AddAsync(params TEntity[] obj);

    /// <summary>
    /// Update one or many entities async
    /// </summary>
    /// <param name="obj">Entities</param>
    /// <returns>Entities affected count</returns>
    Task<int> UpdateAsync(params TEntity[] obj);

    /// <summary>
    /// Delete one or many entities async
    /// </summary>
    /// <param name="obj">Entities</param>
    /// <returns>Entities deleted count</returns>
    Task<int> DeleteAsync(params TEntity[] obj);

    /// <summary>
    /// Delete one or many entities async
    /// </summary>
    /// <param name="obj">Entities keys</param>
    /// <returns>Entities deleted count</returns>
    Task<int> DeleteAsync(params object[] keys);

    /// <summary>
    /// Restore one or many entities async
    /// </summary>
    /// <param name="obj">Entities</param>
    /// <returns>Entities restored count</returns>
    Task<int> RestoreAsync(params TEntity[] obj);
}
