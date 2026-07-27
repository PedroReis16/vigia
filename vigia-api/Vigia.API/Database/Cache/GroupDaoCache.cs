using Vigia.API.Database.CacheContracts;
using Vigia.Cache.Services;
using Vigia.Database.Cache;
using Vigia.Models.Entities;

namespace Vigia.API.Database.Cache;

internal class GroupDaoCache(IInMemoryCacheService cacheService) : RepositoryCache<Group>(cacheService), IGroupDaoCache
{

}