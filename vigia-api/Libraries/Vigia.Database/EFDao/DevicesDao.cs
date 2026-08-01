using Microsoft.EntityFrameworkCore;
using Vigia.Database.CacheContracts;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;



namespace Vigia.Database.EFDao;

internal class DevicesDao(VigiaDbContext context, IDevicesDaoCache? cache = null) : BaseDao<Device>(context, cache), IDevicesDao
{
    protected override IDevicesDaoCache? GetCache() => Cache as IDevicesDaoCache;

    protected override Task ValidateEntityForInsert(params Device[] obj)
    {
        foreach (Device device in obj)
        {
            if (string.IsNullOrWhiteSpace(device.Name))
                throw new EntityValidationException(nameof(device.Name), "O nome do dispositivo é obrigatório", ErrorCodes.DEVICE_NAME_REQUIRED);
            if (string.IsNullOrWhiteSpace(device.MacAddress))
                throw new EntityValidationException(nameof(device.MacAddress), "O endereço MAC do dispositivo é obrigatório", ErrorCodes.MAC_ADDRESS_REQUIRED);
            if (!Vigia.Models.Helpers.Validators.IsValidMacAddress(device.MacAddress))
                throw new EntityValidationException(nameof(device.MacAddress), "O endereço MAC do dispositivo não é válido", ErrorCodes.INVALID_MAC_ADDRESS);
            if (string.IsNullOrWhiteSpace(device.SignPublicKey))
                throw new EntityValidationException(nameof(device.SignPublicKey), "A chave pública do dispositivo é obrigatória", ErrorCodes.SIGN_PUBLIC_KEY_REQUIRED);
            if (!Vigia.Models.Helpers.Validators.IsValidEd25519PublicKeyHex(device.SignPublicKey))
                throw new EntityValidationException(nameof(device.SignPublicKey), "A chave pública do dispositivo não é válida", ErrorCodes.INVALID_SIGN_PUBLIC_KEY);
        }
        return Task.CompletedTask;
    }

    protected override Task ValidateEntityForUpdate(params Device[] obj)
    {
        throw new NotImplementedException();
    }

    public override async Task<Device?> FindAsync(object key, bool track = false)
    {
        Device? result = null;

        if (!track && Cache != null)
        {
            result = Cache.GetEntity(key.ToString()!);
            if (result != null)
                return result;
        }

        DbSet<Device> dbSet = Context.Set<Device>();

        IQueryable<Device> query = dbSet.Where(d => d.Id == (Guid)key && d.DeletedAt == null)
            .Include(d => d.Group);

        result = await query.FirstOrDefaultAsync();

        if (result != null && !track)
            Cache?.AddEntity(result);

        return result;
    }

    public override async Task<int> AddAsync(params Device[] obj)
    {
        await ValidateEntityForInsert(obj);

        DbSet<Device> dbSet = Context.Set<Device>();

        Device newDevice = obj.First();

        Device? trackedDevice = await dbSet
            .Where(d => d.Id == newDevice.Id && d.DeletedAt == null)
            .Include(d => d.Group)
            .FirstOrDefaultAsync();

        if (trackedDevice == null)
            dbSet.Add(newDevice);
        else
        {
            trackedDevice.Name = newDevice.Name;
            trackedDevice.MacAddress = newDevice.MacAddress;
            trackedDevice.SignPublicKey = newDevice.SignPublicKey;
            trackedDevice.UpdatedAt = DateTime.Now.ToUniversalTime();
            trackedDevice.DeletedAt = null;

            dbSet.Update(trackedDevice);
        }

        return await Context.SaveChangesAsync();
    }

    public async Task UpdateDeviceGroupAsync(Device device)
    {
        DbSet<Device> dbSet = Context.Set<Device>();

        Group? userGroup = await Context.Set<Group>()
            .Where(g => g.OwnerId == device.Group!.OwnerId && g.DeletedAt == null)
            .FirstOrDefaultAsync();

        if (userGroup == null)
            throw new EntityValidationException(nameof(Group), $"O grupo relacionado ao usuário {device.Group!.OwnerId} não foi encontrado", ErrorCodes.GROUP_NOT_FOUND);

        device.Group = userGroup;
        device.UpdatedAt = DateTime.Now.ToUniversalTime();

        dbSet.Update(device);

        Cache?.RemoveEntity(device);

        await Context.SaveChangesAsync();
    }

    public async Task<List<Guid>> GetDeviceIdsByGroupAsync(Guid groupId)
    {
        return await Context.Set<Device>()
            .Where(d => d.GroupId == groupId && d.DeletedAt == null)
            .Select(d => d.Id)
            .ToListAsync();
    }

    public async Task<List<Device>> GetUserDevicesAsync(Guid userId, string? nickname = null, DeviceRooms? room = null, bool onlyShared = false, bool onlyOwned = false, int page = 1, int pageSize = 10)
    {
        DbSet<Device> dbSet = Context.Set<Device>();

        IQueryable<Device> query = dbSet
            .Where(
                d => d.DeletedAt == null &&
                d.Group != null && d.Group.LinkedUsers!.Any(u => u.Id == userId)
            )
            .Include(d => d.Group)
            .ThenInclude(g => g!.LinkedUsers!.Where(u => u.DeletedAt == null))
            .AsNoTracking();

        if (!string.IsNullOrWhiteSpace(nickname))
            query = query.Where(
                d => d.Nickname != null && d.Nickname.Contains(nickname) ||
                d.Name.Contains(nickname)
            );

        if (room != null)
            query = query.Where(d => d.Room != null && d.Room == room);

        if (onlyShared)
            query = query.Where(
                d => d.Group!.OwnerId != userId
                );

        if (onlyOwned)
            query = query.Where(d => d.Group!.OwnerId == userId);

        if (page > 0 && pageSize > 0)
            query = query.Skip((page - 1) * pageSize).Take(pageSize);

        return await query.ToListAsync();
    }

    public override async Task<int> UpdateAsync(params Device[] obj)
    {
        DbSet<Device> dbSet = Context.Set<Device>();

        Device updatedDevice = obj.First();

        Device? trackedDevice = await dbSet
            .Where(d => d.Id == updatedDevice.Id && d.DeletedAt == null)
            .FirstOrDefaultAsync();

        if (trackedDevice == null)
            throw new EntityValidationException(nameof(Device), $"O dispositivo '{updatedDevice.Id}' não foi encontrado", ErrorCodes.DEVICE_NOT_FOUND);

        trackedDevice.Nickname = updatedDevice.Nickname ?? trackedDevice.Nickname;
        trackedDevice.Room = updatedDevice.Room ?? trackedDevice.Room;
        trackedDevice.IsClipsEnabled = updatedDevice.IsClipsEnabled;
        trackedDevice.UpdatedAt = DateTime.Now.ToUniversalTime();

        dbSet.Update(trackedDevice);

        Cache?.RemoveEntity(trackedDevice);

        return await Context.SaveChangesAsync();
    }
}