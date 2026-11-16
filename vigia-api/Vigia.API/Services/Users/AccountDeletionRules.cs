using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;
using Vigia.Models.Seed;

namespace Vigia.API.Services.Users;

internal static class AccountDeletionRules
{
    public static bool CanDelete(User user) => !IsSuperAdmin(user);

    public static void EnsureCanDelete(User user)
    {
        if (IsSuperAdmin(user))
            throw new EntityValidationException(
                "account",
                "O super admin não pode apagar a conta",
                ErrorCodes.ACCOUNT_DELETE_FORBIDDEN);
    }

    private static bool IsSuperAdmin(User user) =>
        user.Id == TestDeviceSeed.OwnerId
        || string.Equals(user.Email, TestDeviceSeed.OwnerEmail, StringComparison.OrdinalIgnoreCase);
}
