using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;

namespace Vigia.API.Helpers;

public static class ClaimsPrincipalExtensions
{
    public static Guid GetUserId(this ClaimsPrincipal user)
    {
        string? value = user.FindFirstValue(JwtRegisteredClaimNames.Sub);
        if (string.IsNullOrEmpty(value) || !Guid.TryParse(value, out Guid userId))
            throw new UnauthorizedAccessException("User id claim is missing or invalid");

        return userId;
    }

    public static Guid GetTokenId(this ClaimsPrincipal user)
    {
        string? value = user.FindFirstValue(JwtRegisteredClaimNames.Jti);
        if (string.IsNullOrEmpty(value) || !Guid.TryParse(value, out Guid tokenId))
            throw new UnauthorizedAccessException("Token id claim is missing or invalid");

        return tokenId;
    }

    public static DateTime GetExpiresAt(this ClaimsPrincipal user)
    {
        string? value = user.FindFirstValue(JwtRegisteredClaimNames.Exp);
        if (string.IsNullOrEmpty(value) || !long.TryParse(value, out long exp))
            throw new UnauthorizedAccessException("Expiration claim is missing or invalid");

        return DateTime.UnixEpoch.AddSeconds(exp);
    }
}
