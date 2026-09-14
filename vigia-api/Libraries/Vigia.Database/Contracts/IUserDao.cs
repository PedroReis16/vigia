using Vigia.Models.Entities;

namespace Vigia.Database.Contracts;

public interface IUserDao : IRepository<User>
{
    Task<User?> FindUserByEmailAsync(string email);
    Task<List<User>> GetUsersByGroupAsync(Guid id);
}