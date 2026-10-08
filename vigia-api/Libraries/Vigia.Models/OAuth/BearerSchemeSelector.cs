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

    public static string Select(
        string? authorizationHeader,
        string? accessTokenQuery,
        string? keycloakIssuer,
        IEnumerable<string>? additionalKeycloakIssuers = null)
    {
        if (string.IsNullOrWhiteSpace(keycloakIssuer)
            && !HasIssuer(additionalKeycloakIssuers))
            return LocalJwtScheme;

        string? token = ReadBearerToken(authorizationHeader) ?? NullIfBlank(accessTokenQuery);
        string? issuer = TryReadIssuer(token);
        if (IsKeycloakIssuer(issuer, keycloakIssuer, additionalKeycloakIssuers))
            return KeycloakScheme;

        return LocalJwtScheme;
    }

    private static bool IsKeycloakIssuer(
        string? issuer,
        string? keycloakIssuer,
        IEnumerable<string>? additionalKeycloakIssuers)
    {
        if (string.IsNullOrWhiteSpace(issuer))
            return false;

        if (!string.IsNullOrWhiteSpace(keycloakIssuer)
            && string.Equals(issuer, keycloakIssuer, StringComparison.Ordinal))
            return true;

        if (additionalKeycloakIssuers == null)
            return false;

        foreach (string candidate in additionalKeycloakIssuers)
        {
            if (string.Equals(issuer, candidate, StringComparison.Ordinal))
                return true;
        }

        return false;
    }

    private static bool HasIssuer(IEnumerable<string>? issuers)
    {
        if (issuers == null)
            return false;

        foreach (string issuer in issuers)
        {
            if (!string.IsNullOrWhiteSpace(issuer))
                return true;
        }

        return false;
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
