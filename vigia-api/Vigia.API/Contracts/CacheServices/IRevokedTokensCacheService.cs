namespace Vigia.API.Contracts.CacheServices;

public interface IRevokedTokensCacheService
{
    string? GetToken(Guid tokenId);
    void SaveToken(Guid tokenId, DateTime expirationDate);
}