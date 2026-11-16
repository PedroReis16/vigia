using System.Net;
using Microsoft.AspNetCore.WebUtilities;
using Microsoft.Extensions.Options;
using Vigia.API.Config;
using Vigia.API.Contracts;

namespace Vigia.API.Services;

internal sealed class KeycloakSessionClient(
    HttpClient httpClient,
    IOptions<KeycloakOptions> options,
    ILogger<KeycloakSessionClient> logger) : IKeycloakSessionClient
{
    private readonly HttpClient _httpClient = httpClient;
    private readonly KeycloakOptions _options = options.Value;
    private readonly ILogger<KeycloakSessionClient> _logger = logger;

    public async Task<bool> RevokeRefreshTokenAsync(
        string clientId,
        string refreshToken,
        CancellationToken cancellationToken = default)
    {
        // Reachable URL from the API (may be host.docker.internal) + Host of the token iss.
        string logoutUrl = $"{_options.ResolveLogoutRealmBaseUrl()}/protocol/openid-connect/logout";

        using HttpRequestMessage request = new(HttpMethod.Post, logoutUrl);
        string? hostHeader = _options.ResolveLogoutHostHeader();
        if (!string.IsNullOrEmpty(hostHeader))
            request.Headers.Host = hostHeader;

        request.Content = new FormUrlEncodedContent(
        [
            new KeyValuePair<string, string>("client_id", clientId),
            new KeyValuePair<string, string>("refresh_token", refreshToken),
        ]);

        using HttpResponseMessage response = await _httpClient.SendAsync(request, cancellationToken);

        if (response.IsSuccessStatusCode)
            return true;

        string body = await response.Content.ReadAsStringAsync(cancellationToken);
        _logger.LogWarning(
            "Keycloak rejeitou o logout ({StatusCode}): {Body}",
            (int)response.StatusCode,
            body);

        // Invalid/expired refresh is treated as refusal — caller must not clear FCM.
        if (response.StatusCode is HttpStatusCode.BadRequest or HttpStatusCode.Unauthorized)
            return false;

        response.EnsureSuccessStatusCode();
        return false;
    }

    public string? BuildEndSessionUrl(string? idToken, string? postLogoutRedirectUri)
    {
        if (string.IsNullOrWhiteSpace(idToken) || string.IsNullOrWhiteSpace(postLogoutRedirectUri))
            return null;

        string baseUrl = $"{_options.ResolvePublicRealmBaseUrl()}/protocol/openid-connect/logout";
        return QueryHelpers.AddQueryString(baseUrl, new Dictionary<string, string?>
        {
            ["id_token_hint"] = idToken.Trim(),
            ["post_logout_redirect_uri"] = postLogoutRedirectUri.Trim(),
        });
    }
}
