using Vigia.API.Database.CacheContracts;
using Vigia.API.Database.Contracts;
using Vigia.Database.EFDao;
using Vigia.Models.Entities;

namespace Vigia.API.Database.EFDao;

internal class GroupDao(VigiaDbContext context, IGroupDaoCache? cache = null) : BaseDao<Group>(context, cache), IGroupDao
{
    protected override IGroupDaoCache? GetCache() => Cache as IGroupDaoCache;

    protected override Task ValidateEntityForInsert(params Group[] obj)
    {
        throw new NotImplementedException();
    }

    protected override Task ValidateEntityForUpdate(params Group[] obj)
    {
        throw new NotImplementedException();
    }
}