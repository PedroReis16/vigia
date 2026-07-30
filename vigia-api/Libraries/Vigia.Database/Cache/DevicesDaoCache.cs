using Vigia.Cache.Services;
using Vigia.Models.Entities;
using Vigia.Database.CacheContracts;

namespace Vigia.Database.Cache;

internal class DevicesDaoCache(IInMemoryCacheService cacheService) : RepositoryCache<Device>(cacheService), IDevicesDaoCache
{

}