using Vigia.Cache.Services;
using Vigia.Models.Entities;
using Vigia.Database.CacheContracts;

namespace Vigia.Database.Cache;

internal class UserDaoCache(IRedisCacheService cacheService) : RepositoryCache<User>(cacheService), IUserDaoCache
{

}
