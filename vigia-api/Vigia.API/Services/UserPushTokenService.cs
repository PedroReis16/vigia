using Vigia.API.Contracts;
using Vigia.Database.Contracts;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.Services;

internal class UserPushTokenService(IUserPushTokenDao pushTokenDao) : IUserPushTokenService
{
    private static readonly HashSet<string> AllowedPlatforms = new(StringComparer.OrdinalIgnoreCase)
    {
        "android",
        "ios",
        "web",
    };

    private readonly IUserPushTokenDao _pushTokenDao = pushTokenDao;

    public async Task UpsertPushTokenAsync(Guid userId, string token, string platform)
    {
        ValidatePlatform(platform);
        await _pushTokenDao.UpsertAsync(userId, token, platform.Trim().ToLowerInvariant());
    }

    public async Task DeletePushTokenAsync(Guid userId, string token)
    {
        if (string.IsNullOrWhiteSpace(token))
            throw new EntityValidationException(nameof(token), "O token FCM é obrigatório", ErrorCodes.PUSH_TOKEN_REQUIRED);

        await _pushTokenDao.DeleteByTokenAsync(token);
    }

    private static void ValidatePlatform(string platform)
    {
        if (string.IsNullOrWhiteSpace(platform))
            throw new EntityValidationException(nameof(platform), "A plataforma é obrigatória", ErrorCodes.PUSH_PLATFORM_REQUIRED);

        if (!AllowedPlatforms.Contains(platform.Trim()))
            throw new EntityValidationException(nameof(platform), "Plataforma inválida. Use android, ios ou web.", ErrorCodes.PUSH_PLATFORM_INVALID);
    }
}
