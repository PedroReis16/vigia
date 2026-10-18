using System.Net.Http.Headers;
using System.Text.Json.Nodes;
using Microsoft.Extensions.Options;
using Vigia.API.Config;
using Vigia.API.Contracts;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.Services;

internal sealed class KeycloakAdminClient(
    HttpClient httpClient,
    IOptions<KeycloakOptions> options,
    ILogger<KeycloakAdminClient> logger) : IKeycloakAdminClient
{
    private readonly HttpClient _httpClient = httpClient;
    private readonly KeycloakOptions _options = options.Value;
    private readonly ILogger<KeycloakAdminClient> _logger = logger;
    private readonly SemaphoreSlim _tokenLock = new(1, 1);
    private string? _accessToken;
    private DateTimeOffset _accessTokenExpiresAt;

    public async Task UpdateProfileAsync(
        Guid userId,
        string firstName,
        string lastName,
        string phone,
        CancellationToken cancellationToken = default)
    {
        string token = await AccessTokenAsync(cancellationToken);
        string url = UserUrl(userId);

        using HttpRequestMessage get = Authorized(HttpMethod.Get, url, token);
        using HttpResponseMessage current = await _httpClient.SendAsync(get, cancellationToken);
        if (current.StatusCode == System.Net.HttpStatusCode.NotFound)
            throw new EntityValidationException(nameof(userId), "Usuário não encontrado", ErrorCodes.USER_NOT_FOUND);

        if (!current.IsSuccessStatusCode)
        {
            await LogFailureAsync("leitura", current, cancellationToken);
            throw new EntityValidationException("profile", "Não foi possível atualizar o perfil", ErrorCodes.PROFILE_UPDATE_FAILED);
        }

        JsonNode? node = JsonNode.Parse(await current.Content.ReadAsStringAsync(cancellationToken));
        if (node is not JsonObject user)
            throw new EntityValidationException("profile", "Não foi possível atualizar o perfil", ErrorCodes.PROFILE_UPDATE_FAILED);

        user["firstName"] = firstName;
        user["lastName"] = lastName;
        JsonObject attributes = user["attributes"] as JsonObject ?? new JsonObject();
        attributes["phone"] = new JsonArray(phone);
        user["attributes"] = attributes;

        using HttpRequestMessage put = Authorized(HttpMethod.Put, url, token);
        put.Content = new StringContent(user.ToJsonString(), System.Text.Encoding.UTF8, "application/json");
        using HttpResponseMessage updated = await _httpClient.SendAsync(put, cancellationToken);
        if (updated.IsSuccessStatusCode)
            return;

        await LogFailureAsync("atualização", updated, cancellationToken);
        throw new EntityValidationException("profile", "Não foi possível atualizar o perfil", ErrorCodes.PROFILE_UPDATE_FAILED);
    }

    public async Task DeleteUserAsync(Guid userId, CancellationToken cancellationToken = default)
    {
        string token = await AccessTokenAsync(cancellationToken);
        using HttpRequestMessage request = Authorized(HttpMethod.Delete, UserUrl(userId), token);
        using HttpResponseMessage response = await _httpClient.SendAsync(request, cancellationToken);
        if (response.IsSuccessStatusCode || response.StatusCode == System.Net.HttpStatusCode.NotFound)
            return;

        await LogFailureAsync("exclusão", response, cancellationToken);
        throw new EntityValidationException("profile", "Não foi possível apagar a conta", ErrorCodes.PROFILE_UPDATE_FAILED);
    }

    private string UserUrl(Guid userId) =>
        $"{_options.ResolveAdminServerRoot()}/admin/realms/{_options.ResolveRealmName()}/users/{userId:D}";

    private async Task<string> AccessTokenAsync(CancellationToken cancellationToken)
    {
        if (_accessToken is not null && DateTimeOffset.UtcNow < _accessTokenExpiresAt)
            return _accessToken;

        await _tokenLock.WaitAsync(cancellationToken);
        try
        {
            if (_accessToken is not null && DateTimeOffset.UtcNow < _accessTokenExpiresAt)
                return _accessToken;

            if (string.IsNullOrWhiteSpace(_options.AdminUsername) || string.IsNullOrWhiteSpace(_options.AdminPassword))
                throw new InvalidOperationException("Keycloak:AdminUsername e Keycloak:AdminPassword são obrigatórios para editar o perfil.");

            string clientId = string.IsNullOrWhiteSpace(_options.AdminClientId) ? "admin-cli" : _options.AdminClientId;
            using HttpRequestMessage request = new(
                HttpMethod.Post,
                $"{_options.ResolveAdminServerRoot()}/realms/master/protocol/openid-connect/token")
            {
                Content = new FormUrlEncodedContent(new Dictionary<string, string>
                {
                    ["grant_type"] = "password",
                    ["client_id"] = clientId,
                    ["username"] = _options.AdminUsername,
                    ["password"] = _options.AdminPassword,
                }),
            };

            using HttpResponseMessage response = await _httpClient.SendAsync(request, cancellationToken);
            if (!response.IsSuccessStatusCode)
            {
                await LogFailureAsync("token de administrador", response, cancellationToken);
                throw new EntityValidationException("profile", "Não foi possível atualizar o perfil", ErrorCodes.PROFILE_UPDATE_FAILED);
            }

            JsonNode? payload = JsonNode.Parse(await response.Content.ReadAsStringAsync(cancellationToken));
            string? token = payload?["access_token"]?.GetValue<string>();
            if (string.IsNullOrWhiteSpace(token))
                throw new EntityValidationException("profile", "Não foi possível atualizar o perfil", ErrorCodes.PROFILE_UPDATE_FAILED);

            int expiresIn = payload?["expires_in"]?.GetValue<int>() ?? 60;
            _accessToken = token;
            _accessTokenExpiresAt = DateTimeOffset.UtcNow.AddSeconds(Math.Max(5, expiresIn - 10));
            return token;
        }
        finally
        {
            _tokenLock.Release();
        }
    }

    private static HttpRequestMessage Authorized(HttpMethod method, string url, string token)
    {
        HttpRequestMessage request = new(method, url);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        return request;
    }

    private async Task LogFailureAsync(string action, HttpResponseMessage response, CancellationToken cancellationToken)
    {
        string body = await response.Content.ReadAsStringAsync(cancellationToken);
        _logger.LogWarning(
            "Keycloak recusou a {Action} do perfil: {Status} {Body}",
            action,
            (int)response.StatusCode,
            body);
    }
}
