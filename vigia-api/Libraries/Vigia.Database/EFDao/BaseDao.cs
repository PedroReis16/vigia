using System.Data;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;

namespace Vigia.Database.EFDao;

public class BaseDao<TEntity>(VigiaDbContext context) : IRepository<TEntity> where TEntity : BaseEntity
{
    protected readonly VigiaDbContext Context = context;
    
    public Task<int> AddAsync(params TEntity[] obj)
    {
        throw new NotImplementedException();
    }

    public Task<List<TEntity>> AllAsync(bool track = false)
    {
        throw new NotImplementedException();
    }

    public Task<int> DeleteAsync(params TEntity[] obj)
    {
        throw new NotImplementedException();
    }

    public Task<int> DeleteAsync(params object[] keys)
    {
        throw new NotImplementedException();
    }

    public Task<TEntity?> FindAsync(object key, bool track = false)
    {
        throw new NotImplementedException();
    }

    public Task<int> RestoreAsync(params TEntity[] obj)
    {
        throw new NotImplementedException();
    }

    public Task<int> UpdateAsync(params TEntity[] obj)
    {
        throw new NotImplementedException();
    }
}