using Microsoft.EntityFrameworkCore;
using Vigia.Database.CacheContracts;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.Database.EFDao;

internal class UserPushTokenDao(VigiaDbContext context) : BaseDao<UserPushToken>(context), IUserPushTokenDao
{
    protected override IRepositoryCache<UserPushToken>? GetCache() => null;

    protected override Task ValidateEntityForInsert(params UserPushToken[] obj) => Task.CompletedTask;

    protected override Task ValidateEntityForUpdate(params UserPushToken[] obj) => Task.CompletedTask;

    public async Task UpsertAsync(Guid userId, string token, string platform)
    {
        if (userId == Guid.Empty)
            throw new EntityValidationException(nameof(userId), "O ID do usuário é obrigatório", ErrorCodes.USER_ID_REQUIRED);
        if (string.IsNullOrWhiteSpace(token))
            throw new EntityValidationException(nameof(token), "O token FCM é obrigatório", ErrorCodes.PUSH_TOKEN_REQUIRED);
        if (string.IsNullOrWhiteSpace(platform))
            throw new EntityValidationException(nameof(platform), "A plataforma é obrigatória", ErrorCodes.PUSH_PLATFORM_REQUIRED);

        DbSet<UserPushToken> dbSet = Context.Set<UserPushToken>();
        string normalizedToken = token.Trim();
        string normalizedPlatform = platform.Trim().ToLowerInvariant();

        // Soft-delete (logout) + índice único em Token: reativar em vez de reinserir.
        UserPushToken? existing = await dbSet
            .Where(t => t.Token == normalizedToken)
            .FirstOrDefaultAsync();

        if (existing is null)
        {
            dbSet.Add(new UserPushToken
            {
                UserId = userId,
                Token = normalizedToken,
                Platform = normalizedPlatform,
            });
        }
        else
        {
            existing.UserId = userId;
            existing.Platform = normalizedPlatform;
            existing.UpdatedAt = DateTime.UtcNow;
            existing.DeletedAt = null;
            dbSet.Update(existing);
        }

        await Context.SaveChangesAsync();
    }

    public async Task DeleteByTokenAsync(string token)
    {
        if (string.IsNullOrWhiteSpace(token))
            return;

        DbSet<UserPushToken> dbSet = Context.Set<UserPushToken>();
        string normalizedToken = token.Trim();

        UserPushToken? existing = await dbSet
            .Where(t => t.Token == normalizedToken && t.DeletedAt == null)
            .FirstOrDefaultAsync();

        if (existing is null)
            return;

        existing.DeletedAt = DateTime.UtcNow;
        existing.UpdatedAt = DateTime.UtcNow;
        dbSet.Update(existing);
        await Context.SaveChangesAsync();
    }

    public async Task<List<string>> GetTokensByUserIdsAsync(IEnumerable<Guid> userIds)
    {
        List<Guid> ids = userIds.Distinct().ToList();
        if (ids.Count == 0)
            return [];

        return await Context.Set<UserPushToken>()
            .Where(t => ids.Contains(t.UserId) && t.DeletedAt == null)
            .Select(t => t.Token)
            .Distinct()
            .ToListAsync();
    }

    public async Task DeleteTokensAsync(IEnumerable<string> tokens)
    {
        List<string> tokenList = tokens.Where(t => !string.IsNullOrWhiteSpace(t)).Distinct().ToList();
        if (tokenList.Count == 0)
            return;

        DbSet<UserPushToken> dbSet = Context.Set<UserPushToken>();
        List<UserPushToken> existing = await dbSet
            .Where(t => tokenList.Contains(t.Token) && t.DeletedAt == null)
            .ToListAsync();

        if (existing.Count == 0)
            return;

        DateTime now = DateTime.UtcNow;
        foreach (UserPushToken pushToken in existing)
        {
            pushToken.DeletedAt = now;
            pushToken.UpdatedAt = now;
        }

        dbSet.UpdateRange(existing);
        await Context.SaveChangesAsync();
    }
}
