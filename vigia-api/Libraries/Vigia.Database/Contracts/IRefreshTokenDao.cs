using Vigia.Models.Entities;

namespace Vigia.Database.Contracts;

public interface IRefreshTokenDao : IRepository<RefreshToken>
{
    Task<RefreshToken?> FindByTokenAsync(string refreshToken);
    Task RevokeTokenAsync(string oldRefreshToken, string? newRefreshToken);
}