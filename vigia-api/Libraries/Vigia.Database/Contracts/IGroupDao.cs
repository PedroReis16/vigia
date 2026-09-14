using Vigia.Models.Entities;

namespace Vigia.Database.Contracts;

public interface IGroupDao : IRepository<Group>
{
    Task<Group?> FindWithUsersAsync(Guid groupId, bool track = false);
    Task<int> CountMembersAsync(Guid groupId);
    Task AddUserToGroupAsync(Guid groupId, Guid userId);
    Task RemoveUserFromGroupAsync(Guid groupId, Guid userId);
    Task<bool> IsUserInGroupAsync(Guid groupId, Guid userId);
}
