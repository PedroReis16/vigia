using Vigia.API.Contracts;
using Vigia.API.Models.DTOs.Users;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.Services;

internal sealed class UserLogoutService(
    IKeycloakSessionClient keycloakSession,
    IUserPushTokenService pushTokenService) : IUserLogoutService
{
    private readonly IKeycloakSessionClient _keycloakSession = keycloakSession;
    private readonly IUserPushTokenService _pushTokenService = pushTokenService;

    public async Task<LogoutResponseDTO> LogoutAsync(
        Guid userId,
        string? clientId,
        LogoutRequestDTO request,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(request.RefreshToken))
        {
            throw new EntityValidationException(
                nameof(request.RefreshToken),
                "O refresh token é obrigatório",
                ErrorCodes.REFRESH_TOKEN_REQUIRED);
        }

        if (string.IsNullOrWhiteSpace(clientId))
        {
            throw new EntityValidationException(
                "clientId",
                "Não foi possível determinar o cliente Keycloak (claim azp).",
                ErrorCodes.KEYCLOAK_CLIENT_REQUIRED);
        }

        bool revoked = await _keycloakSession.RevokeRefreshTokenAsync(
            clientId.Trim(),
            request.RefreshToken.Trim(),
            cancellationToken);

        if (!revoked)
        {
            throw new HttpResponseException(
                StatusCodes.Status400BadRequest,
                "O Keycloak recusou o logout da sessão.",
                ErrorCodes.KEYCLOAK_LOGOUT_REJECTED);
        }

        if (!string.IsNullOrWhiteSpace(request.PushToken))
            await _pushTokenService.DeletePushTokenAsync(userId, request.PushToken.Trim());

        string? endSessionUrl = _keycloakSession.BuildEndSessionUrl(
            request.IdToken,
            request.PostLogoutRedirectUri);

        return new LogoutResponseDTO(endSessionUrl);
    }
}
