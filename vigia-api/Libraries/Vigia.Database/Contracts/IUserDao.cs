using Vigia.Models.Entities;

namespace Vigia.Database.Contracts;

public interface IUserDao : IRepository<User>
{
    Task UpsertAsync(User user);

    Task SoftDeleteAsync(Guid userId);

    Task<User?> FindWithGroupsAsync(Guid userId);

    Task<List<User>> GetUsersByGroupAsync(Guid groupId);
}
