namespace Vigia.API.Models.DTOs.Users;

public record LogoutRequestDTO(
    string RefreshToken,
    string? PushToken = null,
    string? IdToken = null,
    string? PostLogoutRedirectUri = null);

public record LogoutResponseDTO(string? EndSessionUrl);
