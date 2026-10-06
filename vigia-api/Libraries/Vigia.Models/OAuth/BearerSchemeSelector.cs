using System.Text.Json;

namespace Vigia.Models.OAuth;

/// <summary>
/// Picks the JWT bearer scheme from the unverified <c>iss</c> claim.
/// Keycloak tokens use the public realm issuer; the API's own tokens use <c>Vigia</c>.
/// </summary>
public static class BearerSchemeSelector
{
    public const string KeycloakScheme = "Keycloak";
    public const string LocalJwtScheme = "OAuth";

    public static string Select(string? authorizationHeader, string? accessTokenQuery, string? keycloakIssuer)
    {
        if (string.IsNullOrWhiteSpace(keycloakIssuer))
            return LocalJwtScheme;

        string? token = ReadBearerToken(authorizationHeader) ?? NullIfBlank(accessTokenQuery);
        string? issuer = TryReadIssuer(token);
        if (string.Equals(issuer, keycloakIssuer, StringComparison.Ordinal))
            return KeycloakScheme;

        return LocalJwtScheme;
    }

    public static string? TryReadIssuer(string? jwt)
    {
        if (string.IsNullOrWhiteSpace(jwt))
            return null;

        string[] parts = jwt.Split('.');
        if (parts.Length < 2 || string.IsNullOrEmpty(parts[1]))
            return null;

        try
        {
            byte[] payload = Base64UrlDecode(parts[1]);
            using JsonDocument document = JsonDocument.Parse(payload);
            if (document.RootElement.TryGetProperty("iss", out JsonElement issuer) &&
                issuer.ValueKind == JsonValueKind.String)
            {
                return issuer.GetString();
            }
        }
        catch (FormatException)
        {
            return null;
        }
        catch (JsonException)
        {
            return null;
        }

        return null;
    }

    private static string? ReadBearerToken(string? authorizationHeader)
    {
        if (string.IsNullOrWhiteSpace(authorizationHeader))
            return null;

        const string prefix = "Bearer ";
        if (!authorizationHeader.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
            return null;

        return NullIfBlank(authorizationHeader[prefix.Length..].Trim());
    }

    private static string? NullIfBlank(string? value) =>
        string.IsNullOrWhiteSpace(value) ? null : value.Trim();

    private static byte[] Base64UrlDecode(string value)
    {
        string padded = value.Replace('-', '+').Replace('_', '/');
        int remainder = padded.Length % 4;
        if (remainder == 1)
            throw new FormatException("Invalid base64url payload.");
        if (remainder > 0)
            padded = padded.PadRight(padded.Length + (4 - remainder), '=');

        return Convert.FromBase64String(padded);
    }
}
