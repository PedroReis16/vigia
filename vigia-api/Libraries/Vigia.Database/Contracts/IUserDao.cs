using Vigia.Models.Entities;

namespace Vigia.Database.Contracts;

public interface IUserDao : IRepository<User>
{
    Task UpsertAsync(User user);

    Task SoftDeleteAsync(Guid userId);
}
