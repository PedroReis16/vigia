using Microsoft.EntityFrameworkCore;
using Vigia.Database.CacheContracts;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.Database.EFDao;

internal class GroupDao(VigiaDbContext context, IGroupDaoCache? cache = null) : BaseDao<Group>(context, cache), IGroupDao
{
    protected override IGroupDaoCache? GetCache() => Cache as IGroupDaoCache;

    protected override Task ValidateEntityForInsert(params Group[] obj)
    {
        foreach (Group group in obj)
        {
            if (group.OwnerId == Guid.Empty)
                throw new EntityValidationException(nameof(group.OwnerId), "O proprietário do grupo é obrigatório", ErrorCodes.USER_ID_REQUIRED);
        }
        return Task.CompletedTask;
    }

    protected override Task ValidateEntityForUpdate(params Group[] obj)
    {
        return Task.CompletedTask;
    }

    public async Task<Group?> FindWithUsersAsync(Guid groupId, bool track = false)
    {
        IQueryable<Group> query = Context.Set<Group>()
            .Where(g => g.Id == groupId && g.DeletedAt == null)
            .Include(g => g.LinkedUsers.Where(u => u.DeletedAt == null));

        if (!track)
            query = query.AsNoTracking();

        return await query.FirstOrDefaultAsync();
    }

    public async Task<int> CountMembersAsync(Guid groupId)
    {
        return await Context.Set<User>()
            .Where(u => u.DeletedAt == null && u.LinkedGroups.Any(g => g.Id == groupId))
            .CountAsync();
    }

    public async Task<bool> IsUserInGroupAsync(Guid groupId, Guid userId)
    {
        return await Context.Set<User>()
            .AnyAsync(u =>
                u.Id == userId &&
                u.DeletedAt == null &&
                u.LinkedGroups.Any(g => g.Id == groupId && g.DeletedAt == null));
    }

    public async Task AddUserToGroupAsync(Guid groupId, Guid userId)
    {
        Group? group = await Context.Set<Group>()
            .Where(g => g.Id == groupId && g.DeletedAt == null)
            .Include(g => g.LinkedUsers)
            .FirstOrDefaultAsync();

        if (group == null)
            throw new EntityValidationException(nameof(Group), "Grupo não encontrado", ErrorCodes.GROUP_NOT_FOUND);

        User? user = await Context.Set<User>()
            .Where(u => u.Id == userId && u.DeletedAt == null)
            .FirstOrDefaultAsync();

        if (user == null)
            throw new EntityValidationException(nameof(User), "Usuário não encontrado", ErrorCodes.USER_NOT_FOUND);

        if (group.LinkedUsers.Any(u => u.Id == userId))
            return;

        group.LinkedUsers.Add(user);
        group.UpdatedAt = DateTime.UtcNow;

        Cache?.RemoveEntity(group);
        await Context.SaveChangesAsync();
    }

    public async Task RemoveUserFromGroupAsync(Guid groupId, Guid userId)
    {
        Group? group = await Context.Set<Group>()
            .Where(g => g.Id == groupId && g.DeletedAt == null)
            .Include(g => g.LinkedUsers)
            .FirstOrDefaultAsync();

        if (group == null)
            throw new EntityValidationException(nameof(Group), "Grupo não encontrado", ErrorCodes.GROUP_NOT_FOUND);

        if (group.OwnerId == userId)
            throw new EntityValidationException(nameof(Group), "O proprietário do grupo não pode ser removido", ErrorCodes.CANNOT_REMOVE_GROUP_OWNER);

        User? user = group.LinkedUsers.FirstOrDefault(u => u.Id == userId);
        if (user == null)
            return;

        group.LinkedUsers.Remove(user);
        group.UpdatedAt = DateTime.UtcNow;

        Cache?.RemoveEntity(group);
        await Context.SaveChangesAsync();
    }
}
