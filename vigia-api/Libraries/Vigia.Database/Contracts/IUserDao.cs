using Vigia.Models.Entities;

namespace Vigia.Database.Contracts;

public interface IUserDao : IRepository<User>
{
    Task<User?> FindUserByEmailAsync(string email);
}