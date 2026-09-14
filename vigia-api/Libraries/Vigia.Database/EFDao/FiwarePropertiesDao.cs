using Vigia.Database.CacheContracts;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;

namespace Vigia.Database.EFDao;

internal class FiwarePropertiesDao(VigiaDbContext context) : BaseDao<FiwareProperties>(context), IFiwarePropertiesDao
{
    protected override IRepositoryCache<FiwareProperties>? GetCache() => null;

    protected override Task ValidateEntityForInsert(params FiwareProperties[] obj)
    {
        return Task.CompletedTask;
    }

    protected override Task ValidateEntityForUpdate(params FiwareProperties[] obj)
    {
        return Task.CompletedTask;
    }


}