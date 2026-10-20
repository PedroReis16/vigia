namespace Vigia.API.Contracts;

public interface IKeycloakSessionClient
{
    /// <summary>
    /// Revoga o refresh token no endpoint OIDC logout do Keycloak.
    /// Retorna true se o Keycloak aceitou; false se recusou.
    /// </summary>
    Task<bool> RevokeRefreshTokenAsync(
        string clientId,
        string refreshToken,
        CancellationToken cancellationToken = default);

    string? BuildEndSessionUrl(string? idToken, string? postLogoutRedirectUri);
}
