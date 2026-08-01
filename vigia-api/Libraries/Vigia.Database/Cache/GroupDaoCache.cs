using Vigia.Cache.Services;
using Vigia.Models.Entities;
using Vigia.Database.CacheContracts;

namespace Vigia.Database.Cache;

internal class GroupDaoCache(IRedisCacheService cacheService) : RepositoryCache<Group>(cacheService), IGroupDaoCache
{

}
