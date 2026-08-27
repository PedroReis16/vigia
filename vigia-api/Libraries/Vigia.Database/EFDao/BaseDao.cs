using System.Data;
using Microsoft.EntityFrameworkCore;
using Vigia.Database.CacheContracts;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;

namespace Vigia.Database.EFDao;

internal abstract class BaseDao<TEntity>(VigiaDbContext context, IRepositoryCache<TEntity>? cache = null) : IRepository<TEntity> where TEntity : BaseEntity
{
    protected VigiaDbContext Context = context;

    protected IRepositoryCache<TEntity>? Cache = cache;

    protected abstract Task ValidateEntityForInsert(params TEntity[] obj);

    protected abstract Task ValidateEntityForUpdate(params TEntity[] obj);

    protected abstract IRepositoryCache<TEntity>? GetCache();

    public virtual async Task<int> AddAsync(params TEntity[] obj)
    {
        DbSet<TEntity> dbSet = Context.Set<TEntity>();
        await ValidateEntityForInsert(obj);
        dbSet.AddRange(obj);
        int result = await Context.SaveChangesAsync();
        return result;
    }

    public virtual async Task<int> UpdateAsync(params TEntity[] obj)
    {
        DbSet<TEntity> dbSet = Context.Set<TEntity>();
        foreach (TEntity entity in obj)
        {
            TEntity? existingEntity = await dbSet
                .AsNoTracking()
                .FirstOrDefaultAsync(e => e.Id.Equals(entity.Id) && e.DeletedAt == null);

            if (existingEntity == null)
                continue;

            await ValidateEntityForUpdate(entity);
            entity.UpdatedAt = DateTime.Now.ToUniversalTime();
            _ = dbSet.Update(entity);
        }

        int result = await Context.SaveChangesAsync();

        if (result > 0)
            Cache?.RemoveEntity(obj);

        return result;
    }

    public virtual async Task<List<TEntity>> AllAsync(bool track = false)
    {
        DbSet<TEntity> dbSet = Context.Set<TEntity>();
        List<TEntity> list = track ?
            await dbSet.Where(d => d.DeletedAt == null).ToListAsync() :
            await dbSet.Where(d => d.DeletedAt == null).AsNoTracking().ToListAsync();
        return list;
    }

    public virtual async Task<int> DeleteAsync(params TEntity[] obj)
    {
        DbSet<TEntity> dbSet = Context.Set<TEntity>();
        foreach (TEntity item in obj)
        {
            item.DeletedAt = item.UpdatedAt = DateTime.Now.ToUniversalTime();
        }
        dbSet.UpdateRange(obj);
        int result = await Context.SaveChangesAsync();

        if (result > 0)
            Cache?.RemoveEntity(obj);

        return result;
    }

    public virtual async Task<int> DeleteAsync(params object[] keys)
    {
        DbSet<TEntity> dbSet = Context.Set<TEntity>();
        foreach (object item in keys)
        {
            TEntity? entity = await dbSet.FindAsync(item);
            if (entity != null)
            {
                entity.DeletedAt = entity.UpdatedAt = DateTime.Now.ToUniversalTime();
                _ = dbSet.Update(entity);
                Cache?.RemoveEntity(entity);
            }
        }
        int result = await Context.SaveChangesAsync();
        return result;
    }

    public virtual async Task<TEntity?> FindAsync(object key, bool track = false)
    {
        TEntity? entity = null;

        if (key != null && Cache != null && !track)
        {
            entity = Cache.GetEntity(key.ToString()!);
            if (entity != null)
                return entity;
        }

        DbSet<TEntity> dbSet = Context.Set<TEntity>();
        entity = track ?
            await dbSet.FindAsync(key) :
            await dbSet.AsNoTracking().FirstOrDefaultAsync(p => p.Id.Equals(key));

        if (entity != null && entity.DeletedAt == null)
        {
            if (!track)
                Cache?.AddEntity(entity);
            return entity;
        }

        return null;
    }

    public async Task<int> RestoreAsync(params TEntity[] obj)
    {
        DbSet<TEntity> dbSet = Context.Set<TEntity>();
        foreach (TEntity item in obj)
        {
            item.DeletedAt = null;
            item.UpdatedAt = DateTime.Now.ToUniversalTime();
        }
        dbSet.UpdateRange(obj);
        int result = await Context.SaveChangesAsync();

        if (result > 0)
            Cache?.RemoveEntity(obj);

        return result;
    }
}