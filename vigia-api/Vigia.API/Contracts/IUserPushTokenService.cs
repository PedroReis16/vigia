namespace Vigia.API.Contracts;

public interface IUserPushTokenService
{
    Task UpsertPushTokenAsync(Guid userId, string token, string platform);
    Task DeletePushTokenAsync(Guid userId, string token);
}
