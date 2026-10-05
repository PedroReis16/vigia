using Microsoft.EntityFrameworkCore;
using Vigia.Database.CacheContracts;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.Database.EFDao;

internal class UserDao(VigiaDbContext context) : BaseDao<User>(context), IUserDao
{
    protected override IRepositoryCache<User>? GetCache() => null;

    protected override Task ValidateEntityForInsert(params User[] obj) => Task.CompletedTask;

    protected override Task ValidateEntityForUpdate(params User[] obj) => Task.CompletedTask;

    public async Task UpsertAsync(User user)
    {
        if (user.Id == Guid.Empty)
            throw new EntityValidationException(nameof(user.Id), "O ID do usuário é obrigatório", ErrorCodes.USER_ID_REQUIRED);

        DbSet<User> dbSet = Context.Set<User>();
        User? existing = await dbSet.FirstOrDefaultAsync(u => u.Id == user.Id);

        if (existing is null)
        {
            user.DeletedAt = null;
            user.CreatedAt = DateTime.UtcNow;
            dbSet.Add(user);
        }
        else
        {
            existing.Email = user.Email;
            existing.Phone = user.Phone;
            existing.DeletedAt = null;
            existing.UpdatedAt = DateTime.UtcNow;
            dbSet.Update(existing);
        }

        await Context.SaveChangesAsync();
    }

    public async Task SoftDeleteAsync(Guid userId)
    {
        if (userId == Guid.Empty)
            return;

        DbSet<User> dbSet = Context.Set<User>();
        User? existing = await dbSet.FirstOrDefaultAsync(u => u.Id == userId && u.DeletedAt == null);
        if (existing is null)
            return;

        DateTime now = DateTime.UtcNow;
        existing.DeletedAt = now;
        existing.UpdatedAt = now;
        dbSet.Update(existing);
        await Context.SaveChangesAsync();
    }

    public async Task<User?> FindWithGroupsAsync(Guid userId)
    {
        if (userId == Guid.Empty)
            return null;

        return await Context.Set<User>()
            .Where(u => u.Id == userId && u.DeletedAt == null)
            .Include(u => u.LinkedGroups)
            .AsNoTracking()
            .FirstOrDefaultAsync();
    }

    public async Task<List<User>> GetUsersByGroupAsync(Guid groupId)
    {
        if (groupId == Guid.Empty)
            return [];

        return await Context.Set<User>()
            .Where(u =>
                u.DeletedAt == null &&
                u.LinkedGroups.Any(g => g.Id == groupId && g.DeletedAt == null))
            .AsNoTracking()
            .ToListAsync();
    }
}
