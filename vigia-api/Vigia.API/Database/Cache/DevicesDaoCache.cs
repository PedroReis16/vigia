using Vigia.API.Database.CacheContracts;
using Vigia.Cache.Services;
using Vigia.Database.Cache;
using Vigia.Models.Entities;

internal class DevicesDaoCache(IInMemoryCacheService cacheService) : RepositoryCache<Device>(cacheService), IDevicesDaoCache
{

}