using System.Text;
using Vigia.Models.OAuth;

namespace Vigia.Models.UnitTests;

public class BearerSchemeSelectorTests
{
    private const string KeycloakIssuer = "http://localhost/auth/realms/vigia";

    [Fact]
    public void Select_UsesKeycloakScheme_WhenIssuerMatches()
    {
        string token = JwtWithIssuer(KeycloakIssuer);

        string scheme = BearerSchemeSelector.Select($"Bearer {token}", null, KeycloakIssuer);

        Assert.Equal(BearerSchemeSelector.KeycloakScheme, scheme);
    }

    [Fact]
    public void Select_UsesLocalScheme_ForApiJwt()
    {
        string token = JwtWithIssuer("Vigia");

        string scheme = BearerSchemeSelector.Select($"Bearer {token}", null, KeycloakIssuer);

        Assert.Equal(BearerSchemeSelector.LocalJwtScheme, scheme);
    }

    [Fact]
    public void Select_ReadsSignalRQueryToken_WhenAuthorizationHeaderIsMissing()
    {
        string token = JwtWithIssuer(KeycloakIssuer);

        string scheme = BearerSchemeSelector.Select(null, token, KeycloakIssuer);

        Assert.Equal(BearerSchemeSelector.KeycloakScheme, scheme);
    }

    [Fact]
    public void Select_UsesLocalScheme_WhenKeycloakIssuerIsNotConfigured()
    {
        string token = JwtWithIssuer(KeycloakIssuer);

        string scheme = BearerSchemeSelector.Select($"Bearer {token}", null, null);

        Assert.Equal(BearerSchemeSelector.LocalJwtScheme, scheme);
    }

    [Fact]
    public void Select_UsesKeycloakScheme_WhenAdditionalIssuerMatches()
    {
        const string lanIssuer = "http://10.0.0.55/auth/realms/vigia";
        string token = JwtWithIssuer(lanIssuer);

        string scheme = BearerSchemeSelector.Select(
            $"Bearer {token}",
            null,
            KeycloakIssuer,
            [lanIssuer]);

        Assert.Equal(BearerSchemeSelector.KeycloakScheme, scheme);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("not-a-jwt")]
    [InlineData("a.!!.c")]
    public void TryReadIssuer_ReturnsNull_ForMalformedTokens(string? jwt)
    {
        Assert.Null(BearerSchemeSelector.TryReadIssuer(jwt));
    }

    private static string JwtWithIssuer(string issuer)
    {
        string payload = Convert.ToBase64String(Encoding.UTF8.GetBytes($"{{\"iss\":\"{issuer}\"}}"))
            .TrimEnd('=')
            .Replace('+', '-')
            .Replace('/', '_');
        return $"header.{payload}.sig";
    }
}
