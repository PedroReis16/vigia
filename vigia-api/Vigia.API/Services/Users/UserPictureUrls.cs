using Vigia.Models.Entities;

namespace Vigia.API.Services.Users;

internal static class UserPictureUrls
{
    public static string? For(User user, string accessToken)
    {
        if (string.IsNullOrWhiteSpace(user.PictureKey))
            return null;

        long version = (user.UpdatedAt ?? user.CreatedAt).Ticks;
        return $"users/{user.Id:D}/picture?accessToken={accessToken}&v={version}";
    }
}
