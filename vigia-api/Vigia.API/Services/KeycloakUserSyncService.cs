using Vigia.API.Contracts;
using Vigia.API.Models.DTOs.Users;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;

namespace Vigia.API.Services;

internal class KeycloakUserSyncService(IUserDao userDao, IUserPushTokenDao pushTokenDao, IGroupDao groupDao) : IKeycloakUserSyncService
{
    private const int FirstNameMaxLength = 64;
    private const int LastNameMaxLength = 64;
    private const int EmailMaxLength = 256;
    private const int PhoneMaxLength = 16;

    private readonly IUserDao _userDao = userDao;
    private readonly IUserPushTokenDao _pushTokenDao = pushTokenDao;
    private readonly IGroupDao _groupDao = groupDao;

    public async Task ApplyAsync(KeycloakUserSyncMessage message)
    {
        if (message.Id == Guid.Empty)
            throw new InvalidOperationException("O ID do usuário é obrigatório.");

        if (string.Equals(message.Operation, "delete", StringComparison.OrdinalIgnoreCase))
        {
            await _userDao.SoftDeleteAsync(message.Id);
            await _pushTokenDao.DeleteByUserIdAsync(message.Id);
            return;
        }

        if (!string.Equals(message.Operation, "upsert", StringComparison.OrdinalIgnoreCase))
            return;

        await _userDao.UpsertAsync(new User
        {
            Id = message.Id,
            Email = Normalize(message.Email, EmailMaxLength),
            Phone = Normalize(message.Phone, PhoneMaxLength),
        });

        await _groupDao.EnsureOwnerMembershipAsync(message.Id);
    }

    private static string Normalize(string? value, int maxLength)
    {
        if (string.IsNullOrWhiteSpace(value))
            return string.Empty;

        string trimmed = value.Trim();
        return trimmed.Length <= maxLength ? trimmed : trimmed[..maxLength];
    }
}
