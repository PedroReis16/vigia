using Vigia.Models.Entities;

namespace Vigia.Database.Contracts;

public interface IUserPushTokenDao : IRepository<UserPushToken>
{
    Task UpsertAsync(Guid userId, string token, string platform);
    Task DeleteByTokenAsync(string token);
    Task<List<string>> GetTokensByUserIdsAsync(IEnumerable<Guid> userIds);
    Task DeleteTokensAsync(IEnumerable<string> tokens);
}
