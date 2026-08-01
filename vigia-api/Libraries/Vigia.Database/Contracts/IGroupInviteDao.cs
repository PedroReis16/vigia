using Vigia.Models.Entities;

namespace Vigia.Database.Contracts;

public interface IGroupInviteDao : IRepository<GroupInvite>
{
    Task<GroupInvite?> FindByTokenAsync(string token, bool track = false);
    Task RevokeActiveInvitesForGroupAsync(Guid groupId);
}
