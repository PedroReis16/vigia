using Vigia.API.Database.CacheContracts;
using Vigia.API.Database.Contracts;
using Vigia.Database.Cache;
using Vigia.Database.EFDao;
using Vigia.Models.Entities;

namespace Vigia.API.Database.EFDao;

internal class DevicesDao(VigiaDbContext context, IDevicesDaoCache? cache = null) : BaseDao<Device>(context, cache), IDevicesDao
{
    protected override IDevicesDaoCache? GetCache() => Cache as IDevicesDaoCache;

    protected override Task ValidateEntityForInsert(params Device[] obj)
    {
        throw new NotImplementedException();
    }

    protected override Task ValidateEntityForUpdate(params Device[] obj)
    {
        throw new NotImplementedException();
    }
}