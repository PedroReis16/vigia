using Microsoft.EntityFrameworkCore;
using Vigia.API.Database.CacheContracts;
using Vigia.API.Database.Contracts;
using Vigia.Database.EFDao;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.Database.EFDao;

internal class UserDao(VigiaDbContext context, IUserDaoCache? cache = null) : BaseDao<User>(context, cache), IUserDao
{
    protected override IUserDaoCache? GetCache() => Cache as IUserDaoCache;

    protected override Task ValidateEntityForInsert(params User[] obj)
    {
        return Task.CompletedTask;
    }

    protected override Task ValidateEntityForUpdate(params User[] obj)
    {
        throw new NotImplementedException();
    }

    public override async Task<User?> FindAsync(object key, bool track = false)
    {
        User? result = null;

        if (!track && Cache != null)
        {
            result = Cache.GetEntity(key.ToString()!);

            if (result != null)
                return result;
        }

        IQueryable<User> query = Context.Set<User>()
            .Where(u => u.Id.Equals(key) && u.DeletedAt == null)
            .Include(u => u.Roles)
            .Include(u => u.LinkedGroups);

        if (!track)
            query = query.AsNoTracking();

        result = await query.FirstOrDefaultAsync();

        if (result != null && !track)
            Cache?.AddEntity(result);

        return result;
    }

    public async Task<User?> FindUserByEmailAsync(string email)
    {
        User? result = null;

        if (Cache != null)
        {
            result = Cache.GetEntity(email);

            if (result != null)
                return result;
        }
        IQueryable<User> query = Context.Set<User>()
            .Where(u => u.Email.Equals(email) && u.DeletedAt == null)
            .Include(u => u.Roles)
            .Include(u => u.LinkedGroups.Where(g => g.DeletedAt == null));

        result = await query.FirstOrDefaultAsync();

        if (result != null)
            Cache?.AddEntity(result);

        return result;
    }

    public override async Task<int> AddAsync(params User[] obj)
    {
        DbSet<User> users = Context.Set<User>();

        User newUser = obj[0];

        User? trackedUser = await users.Where(u => u.Email.Equals(newUser.Email)).FirstOrDefaultAsync();

        List<UserRole> roles = await Context.Set<UserRole>().Where(r => r.Id.Equals("USER")).ToListAsync();

        if (trackedUser == null)
        {
            newUser.Roles = roles;
            users.Add(newUser);
        }
        else
        {
            if (trackedUser.DeletedAt == null)
                throw new EntityValidationException(nameof(User), "O email já está em uso para um outro usuário", ErrorCodes.USER_EMAIL_ALREADY_IN_USE);

            trackedUser.Name = newUser.Name;
            trackedUser.Email = newUser.Email;
            trackedUser.Password = newUser.Password;
            trackedUser.Salt = newUser.Salt;
            trackedUser.UpdatedAt = DateTime.UtcNow;
            trackedUser.DeletedAt = null;

            Cache?.RemoveEntity(trackedUser);
            users.Update(trackedUser);
        }

        return await Context.SaveChangesAsync();
    }
}