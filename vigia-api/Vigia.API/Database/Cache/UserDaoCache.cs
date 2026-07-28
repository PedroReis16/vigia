using Vigia.API.Database.CacheContracts;
using Vigia.Cache.Services;
using Vigia.Database.Cache;
using Vigia.Models.Entities;

namespace Vigia.API.Database.Cache;

internal class UserDaoCache(IInMemoryCacheService cacheService) : RepositoryCache<User>(cacheService), IUserDaoCache
{

}