using Microsoft.EntityFrameworkCore;
using Vigia.API.Database.Contracts;
using Vigia.Database.Cache;
using Vigia.Database.EFDao;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.Database.EFDao;

public class RefreshTokenDao(VigiaDbContext context) : BaseDao<RefreshToken>(context), IRefreshTokenDao
{
    protected override IRepositoryCache<RefreshToken>? GetCache()
    {
        throw new NotImplementedException();
    }

    protected override Task ValidateEntityForInsert(params RefreshToken[] obj)
    {
        foreach (RefreshToken refreshToken in obj)
        {
            if (string.IsNullOrEmpty(refreshToken.Token))
                throw new EntityValidationException(nameof(refreshToken.Token), "O token precisa ser informado para salvar o refresh token", ErrorCodes.TOKEN_REQUIRED);
            if (string.IsNullOrEmpty(refreshToken.RequestIp))
                throw new EntityValidationException(nameof(refreshToken.RequestIp), "O endereço IP precisa ser informado para salvar o refresh token", ErrorCodes.IP_REQUIRED);
            if (refreshToken.ExpiresAt < DateTime.UtcNow)
                throw new EntityValidationException(nameof(refreshToken.ExpiresAt), "A data de expiração precisa ser maior que a data atual para salvar o refresh token", ErrorCodes.EXPIRATION_DATE_INVALID);
            if (refreshToken.UserId == Guid.Empty)
                throw new EntityValidationException(nameof(refreshToken.UserId), "O ID do usuário precisa ser informado para salvar o refresh token", ErrorCodes.USER_ID_REQUIRED);
        }
        return Task.CompletedTask;
    }

    protected override Task ValidateEntityForUpdate(params RefreshToken[] obj)
    {
        throw new NotImplementedException();
    }

    public async Task<RefreshToken?> FindByTokenAsync(string token)
    {
        DbSet<RefreshToken> dbContext = Context.Set<RefreshToken>();

        return await dbContext.Where(rt => rt.Token == token).FirstOrDefaultAsync();
    }

    public async Task RevokeTokenAsync(string oldRefreshToken, string? newRefreshToken = null)
    {
        DbSet<RefreshToken> dbContext = Context.Set<RefreshToken>();

        RefreshToken? trackedToken = await dbContext.Where(rt => rt.Token == oldRefreshToken).FirstOrDefaultAsync();

        if (trackedToken == null)
            return;

        trackedToken.RevokedAt = DateTime.UtcNow;
        trackedToken.ReplacedToken = newRefreshToken;

        dbContext.Update(trackedToken);

        await Context.SaveChangesAsync();
    }
}