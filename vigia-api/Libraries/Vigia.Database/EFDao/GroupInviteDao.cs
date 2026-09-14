using Microsoft.EntityFrameworkCore;
using Vigia.Database.CacheContracts;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.Database.EFDao;

internal class GroupInviteDao(VigiaDbContext context) : BaseDao<GroupInvite>(context), IGroupInviteDao
{
    protected override IRepositoryCache<GroupInvite>? GetCache() => null;

    protected override Task ValidateEntityForInsert(params GroupInvite[] obj)
    {
        foreach (GroupInvite invite in obj)
        {
            if (string.IsNullOrWhiteSpace(invite.Token))
                throw new EntityValidationException(nameof(invite.Token), "O token do convite é obrigatório", ErrorCodes.TOKEN_REQUIRED);
            if (invite.GroupId == Guid.Empty)
                throw new EntityValidationException(nameof(invite.GroupId), "O grupo do convite é obrigatório", ErrorCodes.GROUP_NOT_FOUND);
            if (invite.CreatedByUserId == Guid.Empty)
                throw new EntityValidationException(nameof(invite.CreatedByUserId), "O criador do convite é obrigatório", ErrorCodes.USER_ID_REQUIRED);
            if (invite.ExpiresAt <= DateTime.UtcNow)
                throw new EntityValidationException(nameof(invite.ExpiresAt), "A data de expiração precisa ser maior que a data atual", ErrorCodes.EXPIRATION_DATE_INVALID);
        }
        return Task.CompletedTask;
    }

    protected override Task ValidateEntityForUpdate(params GroupInvite[] obj)
    {
        return Task.CompletedTask;
    }

    public async Task<GroupInvite?> FindByTokenAsync(string token, bool track = false)
    {
        IQueryable<GroupInvite> query = Context.Set<GroupInvite>()
            .Where(i => i.Token == token && i.DeletedAt == null)
            .Include(i => i.Group)
            .ThenInclude(g => g.LinkedUsers);

        if (!track)
            query = query.AsNoTracking();

        return await query.FirstOrDefaultAsync();
    }

    public async Task RevokeActiveInvitesForGroupAsync(Guid groupId)
    {
        List<GroupInvite> activeInvites = await Context.Set<GroupInvite>()
            .Where(i =>
                i.GroupId == groupId &&
                i.DeletedAt == null &&
                i.RevokedAt == null &&
                i.ExpiresAt > DateTime.UtcNow)
            .ToListAsync();

        if (activeInvites.Count == 0)
            return;

        DateTime now = DateTime.UtcNow;
        foreach (GroupInvite invite in activeInvites)
        {
            invite.RevokedAt = now;
            invite.UpdatedAt = now;
        }

        await Context.SaveChangesAsync();
    }
}
